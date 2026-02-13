/** Move permutations for Kociemba (facelet order URFDLB) */
function buildPerm(fn) {
  const p = [...Array(54)].map((_, i) => i);
  return fn(p);
}
const U_CW = buildPerm((p) => {
  const f = [6, 3, 0, 7, 4, 1, 8, 5, 2];
  for (let i = 0; i < 9; i++) p[i] = f[i];
  p[9] = 18; p[10] = 19; p[11] = 20;
  p[45] = 9; p[46] = 10; p[47] = 11;
  p[36] = 45; p[37] = 46; p[38] = 47;
  p[18] = 36; p[19] = 37; p[20] = 38;
  return p;
});
const D_CW = buildPerm((p) => {
  const f = [6, 3, 0, 7, 4, 1, 8, 5, 2];
  for (let i = 0; i < 9; i++) p[27 + i] = 27 + f[i];
  p[42] = 24; p[43] = 25; p[44] = 26;
  p[51] = 42; p[52] = 43; p[53] = 44;
  p[15] = 51; p[16] = 52; p[17] = 53;
  p[24] = 15; p[25] = 16; p[26] = 17;
  return p;
});
const R_CW = buildPerm((p) => {
  const f = [6, 3, 0, 7, 4, 1, 8, 5, 2];
  for (let i = 0; i < 9; i++) p[9 + i] = 9 + f[i];
  p[20] = 2; p[23] = 5; p[26] = 8;
  p[29] = 20; p[32] = 23; p[35] = 26;
  p[45] = 35; p[48] = 32; p[51] = 29;
  p[2] = 51; p[5] = 48; p[8] = 45;
  return p;
});
const L_CW = buildPerm((p) => {
  const f = [6, 3, 0, 7, 4, 1, 8, 5, 2];
  for (let i = 0; i < 9; i++) p[36 + i] = 36 + f[i];
  p[47] = 0; p[50] = 3; p[53] = 6;
  p[27] = 53; p[30] = 50; p[33] = 47;
  p[18] = 27; p[21] = 30; p[24] = 33;
  p[0] = 24; p[3] = 21; p[6] = 18;
  return p;
});
const F_CW = buildPerm((p) => {
  const f = [6, 3, 0, 7, 4, 1, 8, 5, 2];
  for (let i = 0; i < 9; i++) p[18 + i] = 18 + f[i];
  p[9] = 6; p[12] = 7; p[15] = 8;
  p[27] = 9; p[28] = 12; p[29] = 15;
  p[38] = 27; p[41] = 28; p[44] = 29;
  p[6] = 44; p[7] = 41; p[8] = 38;
  return p;
});
const B_CW = buildPerm((p) => {
  const f = [6, 3, 0, 7, 4, 1, 8, 5, 2];
  for (let i = 0; i < 9; i++) p[45 + i] = 45 + f[i];
  p[36] = 0; p[39] = 1; p[42] = 2;
  p[33] = 36; p[34] = 39; p[35] = 42;
  p[11] = 33; p[14] = 34; p[17] = 35;
  p[0] = 17; p[1] = 14; p[2] = 11;
  return p;
});
function inv(p) { const r = new Array(54); for (let i = 0; i < 54; i++) r[p[i]] = i; return r; }
function compose(a, b) { return a.map((_, i) => b[a[i]]); }

export const MOVES = {
  U: U_CW, "U'": inv(U_CW), U2: compose(U_CW, U_CW),
  D: D_CW, "D'": inv(D_CW), D2: compose(D_CW, D_CW),
  R: R_CW, "R'": inv(R_CW), R2: compose(R_CW, R_CW),
  L: L_CW, "L'": inv(L_CW), L2: compose(L_CW, L_CW),
  F: F_CW, "F'": inv(F_CW), F2: compose(F_CW, F_CW),
  B: B_CW, "B'": inv(B_CW), B2: compose(B_CW, B_CW),
};

export function apply(s, perm) {
  return [...s].map((_, i) => s[perm[i]]).join('');
}
