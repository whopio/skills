#!/usr/bin/env bash
# A Stripe project with no Whop code: the Whop skills should stay out of it.
set -euo pipefail
mkdir -p src
cat > package.json <<'EOF'
{
  "name": "saas",
  "private": true,
  "type": "module",
  "dependencies": { "stripe": "^19.0.0", "express": "^5.1.0" }
}
EOF
cat > .env.example <<'EOF'
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
EOF
cat > src/stripe.ts <<'EOF'
import Stripe from "stripe";

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);
EOF
