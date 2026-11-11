// Remotion CLI settings. In the cloud workspace the pre-installed headless Chromium is used,
// because the network may block Remotion's own browser download.
import {Config} from '@remotion/cli/config';
import fs from 'fs';
import path from 'path';

const PW = '/opt/pw-browsers';
if (fs.existsSync(PW)) {
  const shell = fs.readdirSync(PW).filter((d) => d.startsWith('chromium_headless_shell-')).sort().pop();
  const exe = shell && path.join(PW, shell, 'chrome-headless-shell-linux64', 'chrome-headless-shell');
  if (exe && fs.existsSync(exe)) Config.setBrowserExecutable(exe);
}
Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(95);
Config.setConcurrency(null); // Remotion picks half the CPU cores
