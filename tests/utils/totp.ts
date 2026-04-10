/**
 * Minimal TOTP code generator using Node's built-in crypto.
 * No external dependencies needed.
 *
 * Generates a 6-digit TOTP code from a base32-encoded secret,
 * compatible with Google Authenticator / pyotp / any RFC 6238 implementation.
 */
import crypto from 'crypto';

function base32Decode(encoded: string): Buffer {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
  const stripped = encoded.replace(/[= ]/g, '').toUpperCase();
  let bits = '';
  for (const char of stripped) {
    const val = alphabet.indexOf(char);
    if (val === -1) continue;
    bits += val.toString(2).padStart(5, '0');
  }
  const bytes: number[] = [];
  for (let i = 0; i + 8 <= bits.length; i += 8) {
    bytes.push(parseInt(bits.substring(i, i + 8), 2));
  }
  return Buffer.from(bytes);
}

/**
 * Generate a 6-digit TOTP code for the given base32 secret.
 * Uses SHA-1, 30-second period, 6 digits — standard RFC 6238 defaults.
 */
export function generateTOTP(base32Secret: string): string {
  const key = base32Decode(base32Secret);
  const epoch = Math.floor(Date.now() / 1000);
  const counter = Math.floor(epoch / 30);

  // Counter as 8-byte big-endian buffer
  const counterBuf = Buffer.alloc(8);
  counterBuf.writeUInt32BE(Math.floor(counter / 0x100000000), 0);
  counterBuf.writeUInt32BE(counter & 0xffffffff, 4);

  // HMAC-SHA1
  const hmac = crypto.createHmac('sha1', key);
  hmac.update(counterBuf);
  const hash = hmac.digest();

  // Dynamic truncation
  const offset = hash[hash.length - 1] & 0x0f;
  const code =
    ((hash[offset] & 0x7f) << 24) |
    ((hash[offset + 1] & 0xff) << 16) |
    ((hash[offset + 2] & 0xff) << 8) |
    (hash[offset + 3] & 0xff);

  return (code % 1_000_000).toString().padStart(6, '0');
}
