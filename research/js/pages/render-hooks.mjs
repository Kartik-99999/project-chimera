/* Module customization hooks for Node render tests: page modules
 * import { link } from '../app.js', but app.js boots against the DOM.
 * Redirect that specifier to the DOM-free stub. Node >= 20.6. */
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, join } from 'node:path';

const stub = pathToFileURL(join(dirname(fileURLToPath(import.meta.url)), 'app-stub.mjs')).href;

export async function resolve(specifier, context, next) {
  if (specifier === '../app.js' && context.parentURL && context.parentURL.includes('/pages/')) {
    return { url: stub, shortCircuit: true };
  }
  return next(specifier, context);
}
