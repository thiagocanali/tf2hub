import React from 'react';

export default function HomePage() {
  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      justifyContent: 'center', 
      height: '100vh', 
      fontFamily: 'sans-serif',
      background: '#111',
      color: '#fff'
    }}>
      <h1 style={{ color: '#ef6405' }}>👑 TF2Hub Frontend</h1>
      <p>O container do Next.js está respondendo e pronto para o game!</p>
    </div>
  );
}
