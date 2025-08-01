import { auth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

export async function GET(
  request: Request,
  { params }: { params: { pageId: string } }
) {
  try {
    const session = await auth();
    const token = await session.getToken();

    if (!token) {
      return new NextResponse("Unauthorized", { status: 401 });
    }

    const response = await fetch(
      `http://127.0.0.1:8000/api/messages/${params.pageId}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      return new NextResponse(response.statusText, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching messages:", error);
    return new NextResponse("Internal Server Error", { status: 500 });
  }
}
