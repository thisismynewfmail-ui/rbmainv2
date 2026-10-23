/* The event worlds' badge emblems (and any decal their maps paint).

   Loaded straight after textures.js on every page that draws badges -- the
   site's pages and the Game View -- because a badge can turn up anywhere
   (a profile, a toast, somebody's chest in another world).  Every emblem
   is a 128 x 128 sticker drawn with the same inked/stroked helpers as the
   originals in textures.js: keep the picture inside a circle of about 50
   round (64, 64), cream (CREAM) plus one or two strong colours.

   One section per world, in the order the worlds were added. */
(function (global) {
  'use strict';
  var T = global.Textures;
  if (!T || !T.registerEmblem) return;
  var I = T.ink;
  var inked = I.inked, stroked = I.stroked, poly = I.poly, circlePath = I.circlePath;
  var CREAM = I.CREAM, INK = I.INK;
  var emblem = T.registerEmblem, painter = T.registerPainter;

  // @@ event world emblems go above this line @@

  void inked; void stroked; void poly; void circlePath; void CREAM; void INK;
  void emblem; void painter;
})(typeof window !== 'undefined' ? window : globalThis);
