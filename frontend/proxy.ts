import { type NextRequest, NextResponse } from "next/server";

import { isAllowedHost } from "@/lib/host-security";

export function proxy(request: NextRequest) {
  if (
    !isAllowedHost(
      request.headers.get("host"),
      process.env.FRONTEND_ALLOWED_HOSTS,
    )
  ) {
    return new NextResponse("Invalid host", { status: 400 });
  }
  return NextResponse.next();
}

export const config = {
  matcher: "/:path*",
};
