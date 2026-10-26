"""Monta as páginas publicadas do site Getúlio CNH a partir do arquivo-fonte.

Uso: python3 tools/build.py <arquivo-fonte> <pasta-do-site>

Para ativar Google Analytics, Pixel da Meta ou verificação do Search Console,
preencha os valores em config.json e rode o script de novo.
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

SITE = "https://getulio-cnh.onrender.com"
PHONE_DISPLAY = "(31) 2130-0101"
PHONE_E164 = "+553121300101"
SAME_AS = [
    "https://www.facebook.com/profile.php?id=61578643142126",
    "https://www.youtube.com/@getuliocnh",
]

PAGES = [
    {
        "file": "index.html",
        "path": "/",
        "view": "inicio",
        "title": "Tirar ou renovar CNH sem enrolação | Getúlio Vargas CNH",
        "description": "Reprovou na autoescola, não tem tempo ou está com a CNH vencida? Orientação legal para tirar, renovar ou regularizar sua habilitação. Atendimento em todo o Brasil.",
    },
    {
        "file": "memes.html",
        "path": "/memes.html",
        "view": "memes",
        "title": "Memes de autoescola e CNH | Getúlio Vargas CNH",
        "description": "Memes sobre autoescola, baliza, prova prática e renovação da CNH. Ria, marque um amigo e descubra como conquistar sua habilitação.",
    },
]

FAQ = [
    ("Vocês vendem CNH?", "Não. Toda habilitação passa pelas provas oficiais do Detran. O trabalho é orientar e acompanhar você até lá, com o caminho certo para o seu caso."),
    ("Atende na minha cidade?", "Sim. O atendimento é em todo o Brasil pelo WhatsApp. As provas acontecem no Detran do seu estado, e o plano segue as regras dele."),
    ("Ainda preciso de autoescola para tirar a CNH?", "Pelas regras atuais (Resolução Contran nº 1.020/2025), a autoescola não é mais obrigatória para se preparar. Existem outros caminhos, e a gente explica qual faz mais sentido para você."),
    ("Quanto custa?", "Depende do estado e da sua situação. Na primeira conversa você recebe o valor antes de começar qualquer coisa."),
]

FAVICON = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
    "%3Crect width='64' height='64' rx='14' fill='%23F5C518'/%3E"
    "%3Ctext x='32' y='43' text-anchor='middle' font-family='Arial Narrow,Arial,sans-serif' font-weight='900' font-size='30' fill='%2317150A'%3EGV%3C/text%3E%3C/svg%3E"
)


def json_ld(page):
    org = {
        "@context": "https://schema.org",
        "@type": "ProfessionalService",
        "@id": SITE + "/#negocio",
        "name": "Getúlio Vargas CNH",
        "alternateName": "Getúlio CNH",
        "description": PAGES[0]["description"],
        "url": SITE + "/",
        "image": SITE + "/og.png",
        "logo": SITE + "/og.png",
        "telephone": PHONE_E164,
        "areaServed": {"@type": "Country", "name": "Brasil"},
        "availableLanguage": "pt-BR",
        "sameAs": SAME_AS,
        "knowsAbout": ["primeira habilitação", "renovação de CNH", "prova teórica do Detran", "prova prática do Detran", "Resolução Contran 1.020/2025"],
    }
    blocks = [org]
    if page["view"] == "inicio":
        blocks.append({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in FAQ
            ],
        })
    return "\n".join(
        '<script type="application/ld+json">' + json.dumps(b, ensure_ascii=False) + "</script>"
        for b in blocks
    )


def tracking_head(cfg):
    out = []
    if cfg.get("google_site_verification"):
        out.append(f'<meta name="google-site-verification" content="{html.escape(cfg["google_site_verification"])}">')
    if cfg.get("facebook_domain_verification"):
        out.append(f'<meta name="facebook-domain-verification" content="{html.escape(cfg["facebook_domain_verification"])}">')
    ga = cfg.get("ga4_measurement_id")
    if ga:
        out.append(
            f'<script async src="https://www.googletagmanager.com/gtag/js?id={ga}"></script>\n'
            "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
            f"gtag('js',new Date());gtag('config','{ga}');</script>"
        )
    px = cfg.get("meta_pixel_id")
    if px:
        out.append(
            "<script>!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?"
            "n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';"
            "n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}"
            "(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');"
            f"fbq('init','{px}');fbq('track','PageView');</script>\n"
            f'<noscript><img height="1" width="1" style="display:none" alt="" src="https://www.facebook.com/tr?id={px}&ev=PageView&noscript=1"></noscript>'
        )
    return "\n".join(out)


# Mede cliques no WhatsApp e o resultado do teste de placas, se GA4 ou Pixel estiverem ativos.
TRACKING_BODY = """<script>
(function () {
  function send(gaEvent, gaParams, fbEvent, fbParams) {
    try { if (window.gtag) gtag("event", gaEvent, gaParams || {}); } catch (e) {}
    try { if (window.fbq && fbEvent) fbq("track", fbEvent, fbParams || {}); } catch (e) {}
  }
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest('a[href*="wa.me/"]');
    if (!a) return;
    var where = a.id === "form-send" ? "formulario" : (a.closest(".post") ? "meme" : (a.closest(".quiz-card") ? "teste" : "botao"));
    send("generate_lead", { method: "whatsapp", lead_source: where }, "Contact", { content_name: where });
  });
  document.addEventListener("gv:quiz", function (e) {
    send("quiz_complete", { score: e.detail.score }, "Lead", { content_name: "teste_placas", value: e.detail.score });
  });
})();
</script>"""

RESET = "<style>html{-webkit-text-size-adjust:100%}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>"


def build(src_path, out_dir):
    src = Path(src_path).read_text(encoding="utf-8")
    out = Path(out_dir)
    cfg_path = out / "config.json"
    cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}

    # Separa cabeçalho (fontes + estilos) do corpo da página.
    style_end = src.index("</style>") + len("</style>")
    head_src, body_src = src[:style_end], src[style_end:]
    head_src = re.sub(r"<title>.*?</title>\s*", "", head_src, flags=re.S)
    head_src = re.sub(r'<meta name="(description|claude:viewport-fit-sides)"[^>]*>\s*', "", head_src)

    for page in PAGES:
        url = SITE + page["path"]
        t, d = html.escape(page["title"]), html.escape(page["description"])
        head = f"""<!doctype html>
<html lang="pt-BR" data-view="{page['view']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{t}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="theme-color" content="#1A2420">
<link rel="icon" href="{FAVICON}">
<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Getúlio Vargas CNH">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
{json_ld(page)}
{tracking_head(cfg)}
{RESET}
{head_src}
</head>
<body>"""
        body = body_src
        if page["view"] == "memes":
            body = body.replace('<main class="view" id="view-inicio">', '<main class="view" id="view-inicio" hidden>', 1)
            body = body.replace('<main class="view" id="view-memes" hidden>', '<main class="view" id="view-memes">', 1)
        # Links do menu apontam para páginas reais (indexáveis) no site publicado.
        body = body.replace('<a href="#memes" data-nav="memes">', '<a href="/memes.html" data-nav="memes">')
        body = body.replace('<a href="#inicio" data-nav="inicio">', '<a href="/" data-nav="inicio">')
        body = body.replace('<a class="brand" href="#inicio" data-nav="inicio">', '<a class="brand" href="/" data-nav="inicio">')
        (out / page["file"]).write_text(head + body + "\n" + TRACKING_BODY + "\n</body>\n</html>\n", encoding="utf-8")

    today = date.today().isoformat()
    urls = "".join(
        f"  <url><loc>{SITE}{p['path']}</loc><lastmod>{today}</lastmod></url>\n" for p in PAGES
    )
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n",
        encoding="utf-8",
    )
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
