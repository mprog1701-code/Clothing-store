const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

module.exports = {
  ...config,
  server: {
    port: 8081,
  },
  resolver: {
    sourceExts: config.resolver.sourceExts,
    assetExts: [
      ...config.resolver.assetExts,
      'db',
      'mp3',
      'ttf',
      'obj',
      'png',
      'jpg',
    ],
  },
};
