import { Marked, type TokenizerExtension, type Tokens } from 'marked'
import katex from 'katex'
import DOMPurify from 'dompurify'

// Tokenize math before Markdown unescapes backslashes or interprets underscores.
function matchMath(src: string) {
  const open = ['$$', '\\[', '\\(', '$'].find(value => src.startsWith(value))
  if (!open) return
  const close = open === '\\[' ? '\\]' : open === '\\(' ? '\\)' : open
  const display = open === '$$' || open === '\\['
  if (open === '$' && /\s/.test(src[1] || ' ')) return
  for (let i = open.length; i < src.length; i++) {
    if (!display && src[i] === '\n') return
    if (src.startsWith(close, i)) {
      if (open === '$' && (/\s/.test(src[i - 1] || ' ') || /\d/.test(src[i + 1] || ''))) continue
      const text = src.slice(open.length, i)
      if (!text.trim()) return
      return { type: 'math', raw: src.slice(0, i + close.length), text, display }
    }
    if (src[i] === '\\') i++
  }
}

export function renderMarkdown(content: string): string {
  const formulas: string[] = []
  const prefix = `math-${crypto.randomUUID()}-`
  const renderer = (token: Tokens.Generic) => {
    const index = formulas.push(katex.renderToString(token.text, {
      displayMode: token.display,
      throwOnError: false,
      trust: false,
      maxExpand: 1000,
      maxSize: 20,
      strict: 'ignore',
      output: 'htmlAndMathml',
    })) - 1
    return `<span id="${prefix}${index}"></span>`
  }
  const inline: TokenizerExtension = {
    name: 'math', level: 'inline',
    start: src => src.search(/\$|\\\(|\\\[/),
    tokenizer: src => matchMath(src),
  }
  const parser = new Marked({ gfm: true, breaks: false, extensions: [
    { ...inline, renderer },
    {
      name: 'blockMath', level: 'block',
      start: src => src.search(/^ {0,3}(?:\$\$|\\\[)/m),
      tokenizer(src) {
        const leading = src.match(/^ {0,3}/)![0]
        const match = matchMath(src.slice(leading.length))
        if (!match?.display) return
        const trailing = src.slice(leading.length + match.raw.length)
        if (!/^(?:[ \t]*\n|[ \t]*$)/.test(trailing)) return
        return { ...match, type: 'blockMath', raw: leading + match.raw + (trailing.match(/^[ \t]*(?:\n|$)/)?.[0] || '') }
      },
      renderer,
    },
  ] })
  // Sanitize user HTML first. Only trusted KaTeX output is inserted afterward,
  // keeping its layout styles without allowing styles from Markdown authors.
  const clean = DOMPurify.sanitize(parser.parse(content, { async: false }) as string, {
    FORBID_TAGS: ['style', 'iframe', 'form', 'input', 'button'], FORBID_ATTR: ['style'],
  })
  return clean.replace(new RegExp(`<span id="${prefix}(\\d+)"></span>`, 'g'), (_, index) => formulas[Number(index)] || '')
}
