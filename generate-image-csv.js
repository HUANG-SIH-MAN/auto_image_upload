const fs = require('fs');
const path = require('path');

const IMAGE_EXTENSIONS = new Set([
  '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif'
]);

const OUTPUT_FILENAME = 'image_list.csv';
const CSV_HEADER = 'Filename';

const FILES_TO_CLEAR = ['a.csv', 's.csv'];

function clearCsvFiles(dirPath) {
  for (const filename of FILES_TO_CLEAR) {
    const filePath = path.join(dirPath, filename);
    fs.writeFileSync(filePath, '', 'utf8');
  }
}

function isImageFile(filename) {
  const ext = path.extname(filename).toLowerCase();
  return IMAGE_EXTENSIONS.has(ext);
}

function getImageFilenames(dirPath) {
  const entries = fs.readdirSync(dirPath, { withFileTypes: true });
  const filenames = entries
    .filter((entry) => entry.isFile() && isImageFile(entry.name))
    .map((entry) => entry.name)
    .sort();
  return filenames;
}

function main() {
  const targetDir = process.cwd();
  clearCsvFiles(targetDir);
  const imageFilenames = getImageFilenames(targetDir);

  const csvLines = [CSV_HEADER, ...imageFilenames];
  const csvContent = csvLines.join('\n');
  const outputPath = path.join(targetDir, OUTPUT_FILENAME);

  fs.writeFileSync(outputPath, csvContent, 'utf8');
  console.log(`已清空 ${FILES_TO_CLEAR.join('、')}。`);
  console.log(`已產生 ${OUTPUT_FILENAME}，共 ${imageFilenames.length} 個圖片檔。`);
}

main();
