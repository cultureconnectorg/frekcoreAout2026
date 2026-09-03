/**
 * FREKCORE TypeScript SDK — canonical error hierarchy.
 *
 * STATE_7 (docs/architecture/FREKCORE_SDK_CONTRACT_V1.md,
 * FREKCORE_ERROR_CONTRACT_V1.md). Mirrors
 * sdk/python/frekcore_sdk/errors.py exactly: maps an HTTP response status
 * to a typed exception hierarchy every SDK client method raises instead
 * of a bare `Error`.
 *
 * `FrekError` carries the original `Response` on `.response` — an
 * existing caller reading `.status` off a raw fetch rejection can adopt
 * this incrementally; existing clients (`FrekcoreRegistryClient`,
 * `FrekcoreIdentityClient`) still throw a plain `Error` for a network-
 * level failure (no response at all), unchanged — only a *response with
 * a non-2xx status* now throws the canonical hierarchy below (strictly
 * additive, see the SDK contract doc's own "strictly additive" note).
 */

export class FrekError extends Error {
  readonly code: string = "INTERNAL_ERROR";
  readonly status: number;
  readonly response: Response;

  constructor(message: string, response: Response) {
    super(message);
    this.name = new.target.name;
    this.status = response.status;
    this.response = response;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class InvalidRequestError extends FrekError {
  readonly code = "INVALID_REQUEST";
}

export class AuthenticationError extends FrekError {
  readonly code = "AUTHENTICATION_REQUIRED";
}

export class AuthorityError extends FrekError {
  readonly code = "AUTHORITY_DENIED";
}

export class NotFoundError extends FrekError {
  readonly code = "NOT_FOUND";
}

export class ConflictError extends FrekError {
  readonly code = "CONFLICT";
}

export class RateLimitError extends FrekError {
  readonly code = "RATE_LIMITED";
}

export class VerificationError extends FrekError {
  readonly code = "VERIFICATION_FAILED";
}

export class UnsupportedVersionError extends FrekError {
  readonly code = "UNSUPPORTED_VERSION";
}

export class InternalError extends FrekError {
  readonly code = "INTERNAL_ERROR";
}

const STATUS_TO_ERROR: Record<number, new (message: string, response: Response) => FrekError> = {
  400: InvalidRequestError,
  401: AuthenticationError,
  403: AuthorityError,
  404: NotFoundError,
  409: ConflictError,
  422: InvalidRequestError, // FastAPI/Pydantic validation default; see SDK contract doc "SDK error model"
  429: RateLimitError,
};

/** Throws the matching canonical `FrekError` subclass for a non-ok
 * `Response` — a no-op for any ok response, matching `raise_for_status`
 * semantics on the Python side exactly. */
export async function raiseForFrekStatus(response: Response, path: string): Promise<void> {
  if (response.ok) {
    return;
  }
  const ErrorClass = STATUS_TO_ERROR[response.status] ?? (response.status >= 500 ? InternalError : FrekError);
  const message = await errorMessage(response, path);
  throw new ErrorClass(message, response);
}

async function errorMessage(response: Response, path: string): Promise<string> {
  try {
    const body = (await response.clone().json()) as unknown;
    if (body && typeof body === "object") {
      const detail = (body as Record<string, unknown>).detail ?? body;
      if (detail && typeof detail === "object") {
        const message = (detail as Record<string, unknown>).message;
        if (typeof message === "string") return message;
        return JSON.stringify(detail);
      }
      return String(detail);
    }
    return String(body);
  } catch {
    return `FREKCORE request failed: ${path} -> ${response.status}`;
  }
}
