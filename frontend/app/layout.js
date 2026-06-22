// frontend/app/layout.js
export const metadata = {
  title: 'TF2Hub BR — O sistema operacional do TF2 competitivo brasileiro',
  description: 'Analytics, Performance Score, Anti-Cheat e comunidade para o TF2 competitivo BR',
}

export default function RootLayout({ children }) {
  return (
    <html lang="pt-BR">
      <body style={{ margin: 0, padding: 0 }}>{children}</body>
    </html>
  )
}