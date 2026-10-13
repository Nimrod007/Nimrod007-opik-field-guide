import { config } from "dotenv";
import { fileURLToPath } from "node:url";

// Keys come from ./.env or, failing that, a repo-root .env one level up.
config({ path: fileURLToPath(new URL("../.env", import.meta.url)) });
config({ path: fileURLToPath(new URL("../../.env", import.meta.url)) });
