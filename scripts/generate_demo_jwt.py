import argparse
import json
import os
import sys
import time


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from api.auth import create_signed_jwt
from utils.config_handler import auth_conf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a local HS256 JWT for demo/testing.")
    parser.add_argument("--user-id", required=True, help="User id claim")
    parser.add_argument("--city", required=True, help="City claim")
    parser.add_argument("--tenant-id", default="", help="Optional tenant id claim")
    parser.add_argument("--role", action="append", dest="roles", default=[], help="Optional role claim")
    parser.add_argument("--subject", default="", help="Optional JWT subject")
    parser.add_argument(
        "--issuer",
        default=str(auth_conf.get("jwt_issuer", "")).strip(),
        help="Optional issuer claim. Defaults to auth config if present.",
    )
    parser.add_argument(
        "--audience",
        default=str(auth_conf.get("jwt_audience", "")).strip(),
        help="Optional audience claim. Defaults to auth config if present.",
    )
    parser.add_argument("--expires-in", type=int, default=3600, help="Expiration in seconds")
    parser.add_argument(
        "--secret",
        default=(
            os.getenv("APP_JWT_SECRET")
            or os.getenv("JWT_SECRET")
            or str(auth_conf.get("jwt_secret", "")).strip()
        ),
        help="JWT secret. Defaults to APP_JWT_SECRET/JWT_SECRET/auth config.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.secret:
        print("Missing JWT secret. Pass --secret or set APP_JWT_SECRET.", file=sys.stderr)
        return 1

    now = int(time.time())
    claims = {
        "sub": args.subject or args.user_id,
        "user_id": args.user_id,
        "city": args.city,
        "roles": args.roles,
        "iat": now,
        "nbf": now,
        "exp": now + args.expires_in,
    }
    if args.tenant_id:
        claims["tenant_id"] = args.tenant_id
    if args.issuer:
        claims["iss"] = args.issuer
    if args.audience:
        claims["aud"] = args.audience

    token = create_signed_jwt(claims, secret=args.secret, algorithm="HS256")
    print(token)
    print(json.dumps(claims, ensure_ascii=False, indent=2), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
