#!/usr/bin/env bash
# An Express app that already depends on @whop/sdk. The prompt never says "Whop".
set -euo pipefail
mkdir -p src scripts
cat > package.json <<'EOF'
{
  "name": "newsletter",
  "private": true,
  "type": "module",
  "dependencies": { "@whop/sdk": "^2.7.0", "express": "^5.1.0" }
}
EOF
cat > .env.example <<'EOF'
WHOP_API_KEY=
WHOP_WEBHOOK_SECRET=
WHOP_ENVIRONMENT=sandbox
EOF
cat > src/whop.ts <<'EOF'
import { WhopClient, WhopEnvironment } from "@whop/sdk";

export const whop = new WhopClient({
  token: process.env.WHOP_API_KEY!,
  environment: process.env.WHOP_ENVIRONMENT === "sandbox" ? WhopEnvironment.Sandbox : WhopEnvironment.Production,
});
EOF
cat > src/server.ts <<'EOF'
import express from "express";
import { requireUser } from "./auth.js";

const app = express();

// Signed-in readers have req.user = { id, email, whopUserId }.
app.get("/premium", requireUser, async (req, res) => {
  res.json({ issue: "This week's premium issue" });
});

app.listen(3000);
EOF
cat > src/auth.ts <<'EOF'
import type { NextFunction, Request, Response } from "express";

export function requireUser(req: Request, res: Response, next: NextFunction) {
  if (!(req as any).user) return res.status(401).end();
  next();
}
EOF
