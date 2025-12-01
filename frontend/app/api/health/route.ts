import { NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET() {
  try {
    const response = await fetch(`${API_URL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      return NextResponse.json(
        { 
          status: 'unhealthy',
          frontend: 'healthy',
          backend: 'unhealthy',
          error: 'Backend unavailable'
        },
        { status: 503 }
      );
    }
    
    const data = await response.json();
    return NextResponse.json({
      status: 'healthy',
      frontend: 'healthy',
      backend: data,
    });
  } catch (error) {
    console.error('Health check error:', error);
    return NextResponse.json(
      { 
        status: 'degraded',
        frontend: 'healthy',
        backend: 'unreachable',
        error: 'Could not connect to backend'
      },
      { status: 503 }
    );
  }
}
