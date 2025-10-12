'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();
  
  useEffect(() => {
    // No verificar nada, solo mostrar un mensaje
    console.log('Llegó a la página principal');
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold">Dashboard Principal</h1>
      <p>Si ves esto, el login funcionó correctamente.</p>
    </div>
  );
}


