# Kardiograph plug graphics (SVG)

The graphics from the two Kardiograph plugs in Sinus Tach vs SVT v9 (the opener at 0:12 and the end plug at 2:59), exported as standalone SVGs. They are drawn at the size they appear in the 1920x1080 video, in the plugs' colors: Kardiograph coral #E0574F, charcoal #222222, grey #6A6A6A, teal #2E9C8F for the score.

Text is converted to outlines (Manrope for the wordmark, headings and kickers; Inter for everything else), so the files look right without the fonts installed. To change a word, retype it in Manrope or Inter at the same size. Groups have readable ids, which Illustrator shows as layer names: for example mark, mark-tile, mark-wave, wordmark, call-to-action, strip-trace, strip-grid-1mm, strip-grid-5mm, calipers and chip-svt-picked.

Every ECG strip is lead II from Kardiograph's own EKG engine, at true scale: 25 mm/s and 10 mm/mV, at 9.6 px per mm. A 6 s strip is 1440 x 288 px. The paper has 1 mm and 5 mm grid lines and the "II" lead label.

## Brand
- kardiograph-mark.svg: the mark alone, a coral rounded square with the white wave (132 px).
- kardiograph-lockup.svg: the mark with the "Kardiograph" wordmark and "by Medzcool".
- kardiograph-lockup-brought-to-you-by.svg: the opener's lockup, with "This video is brought to you by" above it.
- kardiograph-lockup-url-try-it-free.svg: the closing lockup, with the kardiograph.medzcool.com and Try it free pills.
- url-pill.svg, try-it-free-pill.svg: the two call-to-action pills on their own.
- corner-label-practice.svg, corner-label-true-scale.svg: the small corner mark with its kicker, as used at the top left of each scene.

## ECG strips (6 s, lead II)
- ecg-strip-sinus.svg: normal sinus rhythm, 72 bpm.
- ecg-strip-svt.svg: SVT, 183 bpm (the strip in the opener's practice card).
- ecg-strip-afib.svg: atrial fibrillation.
- ecg-strip-flutter.svg: atrial flutter.
- ecg-strip-avb1.svg: 1st-degree AV block.
- ecg-strip-mobitz1.svg: Mobitz I.
- ecg-strip-sinus-calipers.svg: the sinus strip with calipers open from one R wave to the next and the readout "832 ms · 72 bpm" (end plug, "calipers").

## Practice (opener)
- practice-card-svt.svg: the SVT strip on its white card with the soft shadow.
- practice-answers.svg: the three answer chips before a pick: Sinus, Atrial flutter, SVT.
- practice-answers-scored.svg: after the click: SVT picked (coral, with a check) and the "100% Rhythm: SVT" score.
- cursor-arrow.svg: the pointer that clicks SVT. Its tip is at 0,0.

## End plug
- tile-course.svg: "Course, 7 modules, 21 lessons" with the book icon.
- tile-practice.svg: "Practice, 5 decks, scored" with the clipboard icon.
- new-tracing-pill.svg: the "New tracing" pill with the rotate icon.
- rhythm-grid.svg: the six rhythms as 3 s strips on cards with their names, as on "endless".

## Icons (24 px, one color)
- icon-book.svg, icon-clipboard.svg, icon-rotate.svg, icon-check.svg: line icons in currentColor, so they take the color of whatever they're placed in.

The cards and tiles use an SVG drop-shadow filter (0 8 px, 24 px blur, 8 to 10% charcoal). Illustrator keeps it as an SVG filter. Delete the filter if you want flat shapes.

Made by make_svgs.py in the motion-graphics repo (videos/Sinus Tach vs SVT/3-board/kardiograph-plug/), from the same values the Remotion plugs use.
