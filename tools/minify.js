// Compacta o CSS e o JS embutidos nas páginas publicadas (não mexe em JSON-LD nem no conteúdo).
// uso: NODE_PATH=<pasta com terser e clean-css>/node_modules node tools/minify.js index.html memes.html
const fs = require('fs');
const { minify } = require('terser');
const CleanCSS = require('clean-css');
(async () => {
  for (const file of process.argv.slice(2)) {
    let html = fs.readFileSync(file, 'utf8');
    const before = html.length;
    html = html.replace(/<style>([\s\S]*?)<\/style>/g, (m, css) => '<style>' + new CleanCSS({ level: 1 }).minify(css).styles + '</style>');
    const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
    for (const s of scripts) {
      const out = await minify(s[1], { compress: true, mangle: true, format: { comments: false } });
      html = html.replace(s[0], () => '<script>' + out.code + '</script>');
    }
    fs.writeFileSync(file, html);
    console.log(file, before, '->', html.length);
  }
})();
