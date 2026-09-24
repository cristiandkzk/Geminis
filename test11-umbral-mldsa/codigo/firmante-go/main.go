// Test 11 — firmante: produce firmas ML-DSA-44 que la maquina de §6.6 despues verifica.
//
// Usa el prototipo de umbral de Mithril (Celi, del Pino, Espitau, Niot, Prest; USENIX Security '26)
// **sin modificarlo**, en el commit fijado en `../mithril` (ver RESULTS.md, "Reproducir"). Solo se
// llama al paquete `thmldsa44`; no se usa la parte de red (`go-libp2p`), y este binario no abre
// ningun socket ni escribe ningun archivo: todo sale por stdout.
//
//	firmante umbral   <t> <n> <activos-csv> <semilla-hex-32> <mensaje-hex> <repeticiones>
//	firmante simple   <semilla-hex-32> <mensaje-hex>
//	firmante insuficiente <t> <n> <semilla-hex-32> <mensaje-hex>
//
// `umbral` reparte una clave ML-DSA-44 en `n` partes con umbral `t`, firma con el subconjunto
// `activos` (ids 0-based) y por cada repeticion imprime una linea `clave=.. firma=.. intentos=..`.
// La clave publica y la firma son las de FIPS 204 (1312 y 2420 bytes): lo que sale de aca es lo
// que entra tal cual al verificador de la cadena.
package main

import (
	"encoding/hex"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/cloudflare/circl/sign/mldsa/mldsa44"
	"github.com/cloudflare/circl/sign/thmldsa/thmldsa44"
)

const maxIntentos = 1000

func die(format string, a ...any) {
	fmt.Fprintf(os.Stderr, format+"\n", a...)
	os.Exit(2)
}

func unhex(s string) []byte {
	b, err := hex.DecodeString(s)
	if err != nil {
		die("hex invalido: %v", err)
	}
	return b
}

func seed32(s string) [32]byte {
	b := unhex(s)
	if len(b) != 32 {
		die("la semilla debe tener 32 bytes, tiene %d", len(b))
	}
	var out [32]byte
	copy(out[:], b)
	return out
}

func mascara(activos []int, n int) uint8 {
	var m uint8
	for _, id := range activos {
		if id < 0 || id >= n {
			die("id activo fuera de rango: %d", id)
		}
		m |= 1 << uint(id)
	}
	return m
}

// firmarUmbral corre el protocolo de tres rondas hasta que Combine acepta (cada intento tiene
// probabilidad de exito < 1: es la rejection sampling de ML-DSA repartida). Devuelve la firma,
// el numero de intentos, el tiempo total y los bytes que sale cada parte activa por intento.
func firmarUmbral(sks []thmldsa44.PrivateKey, pk *thmldsa44.PublicKey, params *thmldsa44.ThresholdParams,
	activos []int, mask uint8, msg []byte) (sig []byte, intentos int, dur time.Duration, bytesParte int) {

	sig = make([]byte, thmldsa44.SignatureSize)
	inicio := time.Now()
	for intentos = 1; intentos <= maxIntentos; intentos++ {
		na := len(activos)
		st1 := make([]thmldsa44.StRound1, na)
		h1 := make([][]byte, na)
		for j, id := range activos {
			var err error
			h1[j], st1[j], err = thmldsa44.Round1(&sks[id], params)
			if err != nil {
				die("Round1: %v", err)
			}
		}
		st2 := make([]thmldsa44.StRound2, na)
		w := make([][]byte, na)
		for j, id := range activos {
			var err error
			w[j], st2[j], err = thmldsa44.Round2(&sks[id], mask, msg, nil, h1, &st1[j], params)
			if err != nil {
				die("Round2: %v", err)
			}
		}
		resps := make([][]byte, na)
		for j, id := range activos {
			var err error
			resps[j], err = thmldsa44.Round3(&sks[id], w, &st2[j], params)
			if err != nil {
				die("Round3: %v", err)
			}
		}
		bytesParte = len(h1[0]) + len(w[0]) + len(resps[0])
		if thmldsa44.Combine(pk, msg, nil, w, resps, sig, params) {
			return sig, intentos, time.Since(inicio), bytesParte
		}
	}
	die("no se obtuvo firma en %d intentos", maxIntentos)
	return
}

func cmdUmbral(a []string) {
	if len(a) != 6 {
		die("uso: firmante umbral <t> <n> <activos-csv> <semilla> <mensaje-hex> <repeticiones>")
	}
	t, _ := strconv.Atoi(a[0])
	n, _ := strconv.Atoi(a[1])
	var activos []int
	for _, p := range strings.Split(a[2], ",") {
		id, err := strconv.Atoi(p)
		if err != nil {
			die("activos invalidos: %v", err)
		}
		activos = append(activos, id)
	}
	seed := seed32(a[3])
	msg := unhex(a[4])
	reps, _ := strconv.Atoi(a[5])

	params, err := thmldsa44.GetThresholdParams(uint8(t), uint8(n))
	if err != nil {
		die("parametros: %v", err)
	}
	pk, sks := thmldsa44.NewThresholdKeysFromSeed(&seed, params)
	mask := mascara(activos, n)
	if len(activos) < t {
		die("hay %d activos y el umbral es %d", len(activos), t)
	}
	clave := pk.Bytes()
	fmt.Printf("# t=%d n=%d activos=%v K=%d clave=%dB firma=%dB\n", t, n, activos, params.K, len(clave), thmldsa44.SignatureSize)
	for r := 0; r < reps; r++ {
		sig, intentos, dur, bytesParte := firmarUmbral(sks, pk, params, activos, mask, msg)
		nativoGo := thmldsa44.Verify(pk, msg, nil, sig)
		fmt.Printf("clave=%x firma=%x intentos=%d ms=%.3f bytes_parte=%d go_verifica=%d\n",
			clave, sig, intentos, float64(dur.Microseconds())/1000.0, bytesParte, b2i(nativoGo))
	}
}

// cmdSimple firma con ML-DSA-44 **de un solo firmante**, del mismo fork y con el mismo mensaje:
// es el ancla externa. Si la maquina acepta esta y la de `umbral`, la diferencia de pasos entre
// una y otra es cero por construccion, no por casualidad del protocolo de umbral.
func cmdSimple(a []string) {
	if len(a) != 2 {
		die("uso: firmante simple <semilla> <mensaje-hex>")
	}
	seed := seed32(a[0])
	msg := unhex(a[1])
	pk, sk := mldsa44.NewKeyFromSeed(&seed)
	sig := make([]byte, mldsa44.SignatureSize)
	if err := mldsa44.SignTo(sk, msg, nil, false, sig); err != nil {
		die("SignTo: %v", err)
	}
	ok := mldsa44.Verify(pk, msg, nil, sig)
	fmt.Printf("clave=%x firma=%x go_verifica=%d\n", pk.Bytes(), sig, b2i(ok))
}

// cmdInsuficiente prueba dos formas de quedarse por debajo del umbral, y cuenta cuantas firmas
// aceptadas salen (tiene que ser 0). No es una prueba de seguridad —esa esta en el paper—: es lo
// que se puede observar desde la API.
//
//	(a) UNA sola parte activa con t = 2. El prototipo **no devuelve un error: hace panic** (indice
//	    fuera de rango en `recoverShare`), asi que se captura y se cuenta aparte. Es un hallazgo de
//	    robustez del prototipo, no de la firma.
//	(b) Dos partes firman completo, pero `Combine` recibe UNA sola respuesta: la guarda de la API.
func cmdInsuficiente(a []string) {
	if len(a) != 4 {
		die("uso: firmante insuficiente <t> <n> <semilla> <mensaje-hex>")
	}
	t, _ := strconv.Atoi(a[0])
	n, _ := strconv.Atoi(a[1])
	seed := seed32(a[2])
	msg := unhex(a[3])
	params, err := thmldsa44.GetThresholdParams(uint8(t), uint8(n))
	if err != nil {
		die("parametros: %v", err)
	}
	pk, sks := thmldsa44.NewThresholdKeysFromSeed(&seed, params)
	const intentos = 50
	aceptadas, panicos := 0, 0
	sig := make([]byte, thmldsa44.SignatureSize)

	// (a) una sola parte activa
	for i := 0; i < intentos; i++ {
		func() {
			defer func() {
				if recover() != nil {
					panicos++
				}
			}()
			mask := mascara([]int{0}, n)
			h1, st1, err := thmldsa44.Round1(&sks[0], params)
			if err != nil {
				return
			}
			w, st2, err := thmldsa44.Round2(&sks[0], mask, msg, nil, [][]byte{h1}, &st1, params)
			if err != nil {
				return
			}
			resp, err := thmldsa44.Round3(&sks[0], [][]byte{w}, &st2, params)
			if err != nil {
				return
			}
			if thmldsa44.Combine(pk, msg, nil, [][]byte{w}, [][]byte{resp}, sig, params) &&
				thmldsa44.Verify(pk, msg, nil, sig) {
				aceptadas++
			}
		}()
	}

	// (b) dos partes firman, Combine recibe una sola respuesta
	aceptadasB := 0
	activos := []int{0, 1}
	mask := mascara(activos, n)
	for i := 0; i < intentos; i++ {
		st1 := make([]thmldsa44.StRound1, 2)
		h1 := make([][]byte, 2)
		for j, id := range activos {
			h1[j], st1[j], _ = thmldsa44.Round1(&sks[id], params)
		}
		st2 := make([]thmldsa44.StRound2, 2)
		w := make([][]byte, 2)
		for j, id := range activos {
			w[j], st2[j], _ = thmldsa44.Round2(&sks[id], mask, msg, nil, h1, &st1[j], params)
		}
		resps := make([][]byte, 2)
		for j, id := range activos {
			resps[j], _ = thmldsa44.Round3(&sks[id], w, &st2[j], params)
		}
		if thmldsa44.Combine(pk, msg, nil, w, resps[:1], sig, params) {
			aceptadasB++
		}
	}
	fmt.Printf("t=%d n=%d intentos=%d una_parte_activa_firmas=%d una_parte_activa_panicos=%d una_respuesta_firmas=%d firmas_aceptadas=%d\n",
		t, n, intentos, aceptadas, panicos, aceptadasB, aceptadas+aceptadasB)
}

func b2i(b bool) int {
	if b {
		return 1
	}
	return 0
}

func main() {
	if len(os.Args) < 2 {
		die("uso: firmante umbral|simple|insuficiente ...")
	}
	switch os.Args[1] {
	case "umbral":
		cmdUmbral(os.Args[2:])
	case "simple":
		cmdSimple(os.Args[2:])
	case "insuficiente":
		cmdInsuficiente(os.Args[2:])
	default:
		die("subcomando desconocido: %s", os.Args[1])
	}
}
