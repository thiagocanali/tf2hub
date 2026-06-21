export function getApiUrl() {
  // Se estiver no navegador
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    // Se estiver no Codespaces, troca o sufixo da porta 3000 para 8000
    if (hostname.includes('app.github.dev')) {
      return `https://${hostname.replace('-3000', '-8000')}`;
    }
  }
  // Fallback para docker local
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
}

export async function getPlayer(steamid: string) {
    const res = await fetch(`${getApiUrl()}/api/players/${steamid}`);
    return res.ok ? res.json() : null;
}

export async function syncPlayer(steamid: string) {
    const res = await fetch(`${getApiUrl()}/api/sync/${steamid}`, { method: 'POST' });
    return res.json();
}

export async function getRanking() {
    const res = await fetch(`${getApiUrl()}/api/ranking`);
    return res.ok ? res.json() : [];
}