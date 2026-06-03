const B2 = require('backblaze-b2');

class B2Client {
  constructor(config) {
    this.b2 = new B2({
      applicationKeyId: config.applicationKeyId,
      applicationKey: config.applicationKey,
    });
    this.bucketName = config.bucketName;
    this._bucketId = null;
  }

  async authorize() {
    const response = await this.b2.authorize();
    console.log('✅ B2 授權成功');
    return response;
  }

  async getOrCreateBucket() {
    const response = await this.b2.getBucket({ bucketName: this.bucketName });
    const bucket = response.data.buckets?.[0];
    if (bucket) {
      this._bucketId = bucket.bucketId;
      console.log(`✅ 找到 Bucket: ${this.bucketName}`);
      return bucket;
    }
    const created = await this.b2.createBucket({
      bucketName: this.bucketName,
      bucketType: 'allPublic',
    });
    this._bucketId = created.data.bucketId;
    console.log(`✅ 已建立 Bucket: ${this.bucketName} (公開)`);
    return created.data;
  }

  async uploadJson(data, remotePath) {
    if (!this._bucketId) throw new Error('尚未授權，請先呼叫 authorize()');

    const content = JSON.stringify(data, null, 2);
    const buffer = Buffer.from(content, 'utf-8');

    const uploadUrl = await this.b2.getUploadUrl({ bucketId: this._bucketId });
    const { uploadUrl: url, authorizationToken } = uploadUrl.data;

    const result = await this.b2.uploadFile({
      uploadUrl: url,
      uploadAuthToken: authorizationToken,
      fileName: remotePath,
      data: buffer,
      mime: 'application/json',
      hash: null,
    });

    console.log(`✅ 已上傳: ${remotePath}`);
    return result.data;
  }

  async uploadImage(filePath, remotePath) {
    if (!this._bucketId) throw new Error('尚未授權，請先呼叫 authorize()');

    const fs = require('fs');
    const buffer = fs.readFileSync(filePath);

    const uploadUrl = await this.b2.getUploadUrl({ bucketId: this._bucketId });
    const { uploadUrl: url, authorizationToken } = uploadUrl.data;

    const ext = filePath.split('.').pop().toLowerCase();
    const mimeMap = { jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', webp: 'image/webp' };
    const mime = mimeMap[ext] || 'application/octet-stream';

    const result = await this.b2.uploadFile({
      uploadUrl: url,
      uploadAuthToken: authorizationToken,
      fileName: remotePath,
      data: buffer,
      mime: mime,
      hash: null,
    });

    console.log(`✅ 已上傳圖片: ${remotePath}`);
    return result.data;
  }

  getPublicUrl(fileName) {
    return `https://f002.backblazeb2.com/file/${this.bucketName}/${fileName}`;
  }
}

module.exports = B2Client;
