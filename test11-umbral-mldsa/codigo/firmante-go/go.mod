module firmante

go 1.22.0

// El prototipo de Mithril, sin tocar, en el commit fijado en RESULTS.md ("Reproducir"):
//   git clone https://github.com/Threshold-ML-DSA/Threshold-ML-DSA ../mithril
//   git -C ../mithril checkout 66e269e75dd8f5d722675a3d276a1aedc58bc4ef
// Su modulo se llama `github.com/cloudflare/circl` (es un fork de CIRCL con el paquete thmldsa).
require github.com/cloudflare/circl v1.6.0

require golang.org/x/sys v0.10.0 // indirect

replace github.com/cloudflare/circl => ../mithril/implementation
