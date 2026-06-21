// Troca code por access token → busca user.id → salva no backend
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const code = searchParams.get('code')
  
  const tokenRes = await fetch('https://discord.com/api/oauth2/token', {
    method: 'POST',
    body: new URLSearchParams({
      client_id: process.env.DISCORD_CLIENT_ID!,
      client_secret: process.env.DISCORD_CLIENT_SECRET!,
      code: code!,
      grant_type: 'authorization_code',
      redirect_uri: process.env.DISCORD_REDIRECT_URI!,
    })
  })
  
  const { access_token } = await tokenRes.json()
  const userRes = await fetch('https://discord.com/api/users/@me', {
    headers: { Authorization: `Bearer ${access_token}` }
  })
  const discordUser = await userRes.json()
  
  // Salva discord_id no perfil do jogador no backend
  await fetch(`${process.env.BACKEND_URL}/players/link-discord`, {
    method: 'POST',
    body: JSON.stringify({ discord_id: discordUser.id, discord_username: discordUser.username })
  })
  
  return redirect('/profile?linked=discord')
}