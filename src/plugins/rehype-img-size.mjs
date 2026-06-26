import { visit } from 'unist-util-visit';
import { imageSize } from 'image-size';
import path from 'path';
import fs from 'fs';

const publicDir = path.resolve('public');

export default function rehypeImgSize() {
  return (tree) => {
    visit(tree, 'element', (node) => {
      if (node.tagName !== 'img') return;
      const props = node.properties || {};
      if (props.width && props.height) return;

      const src = props.src;
      if (!src || typeof src !== 'string' || !src.startsWith('/images/')) return;

      const filePath = path.join(publicDir, src);
      try {
        const buf = fs.readFileSync(filePath);
        const { width, height } = imageSize(buf);
        if (width && height) {
          props.width = String(width);
          props.height = String(height);
        }
      } catch {
        // file missing or unreadable — skip
      }
    });
  };
}
