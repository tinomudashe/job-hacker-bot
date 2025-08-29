import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json(
    { 
      status: "ok",
      service: "job-hacker-bot",
      timestamp: new Date().toISOString()
    },
    { 
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
      }
    }
  );
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
    },
  });
}