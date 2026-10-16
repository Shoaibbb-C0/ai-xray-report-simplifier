export function isPatientRoute(path) {
  return ['/map', '/history', '/profile'].some(root => path === root || path.startsWith(`${root}/`));
}

export function safeReturnPath(path) {
  return typeof path === 'string' && /^\/(map|history|profile)(\/[^\\]*)?$/.test(path) ? path : '/map';
}

export function authState(session) {
  return session?.user ? 'authenticated' : 'anonymous';
}
