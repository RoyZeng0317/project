const mysql = require('mysql');
const path = require('path');
const fs = require('fs');
const B2Client = require('./b2Client');

// ---------- 載入設定 ----------
const configPath = path.join(__dirname, 'config.json');
if (!fs.existsSync(configPath)) {
  console.error('❌ 找不到 config.json，請複製 config.example.json 並填入憑證');
  process.exit(1);
}
const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));

// ---------- MySQL 連線 ----------
const db = mysql.createConnection(config.mysql);

function query(sql) {
  return new Promise((resolve, reject) => {
    db.query(sql, (err, results) => {
      if (err) return reject(err);
      resolve(results);
    });
  });
}

// ---------- B2 上傳 ----------
async function deployParkingLots(b2) {
  // 1. 從 MySQL 讀取停車場資料
  const rows = await query('SELECT * FROM parking_lots ORDER BY id');
  console.log(`📦 從 MySQL 讀取 ${rows.length} 筆停車場資料`);

  // 2. 轉換為前端 friendly 格式
  const parkingLots = rows.map((row) => ({
    id: row.id,
    name: row.name,
    address: row.address,
    lat: row.lat,
    lng: row.lng,
    totalSlots: row.total_slots,
    availableSlots: row.available_slots,
    feePerHour: row.fee_per_hour,
    imageUrl: b2.getPublicUrl(`parking_lots/images/${row.id}.jpg`),
  }));

  // 3. 上傳 JSON 到 B2
  await b2.uploadJson(parkingLots, 'parking_lots/data.json');

  // 4. 上傳 SQL 備份到 B2
  const sqlPath = path.join(__dirname, '..', '..', 'data', 'parking_lots.sql');
  if (fs.existsSync(sqlPath)) {
    const sqlBuffer = fs.readFileSync(sqlPath, 'utf-8');
    await b2.uploadJson(
      { sql: sqlBuffer, exportedAt: new Date().toISOString() },
      'parking_lots/schema.json'
    );
  }

  // 5. 上傳圖片
  const imgDir = path.join(__dirname, '..', '..', 'data', 'img');
  if (fs.existsSync(imgDir)) {
    const files = fs.readdirSync(imgDir).filter((f) => /\.(jpg|jpeg|png|webp)$/i.test(f));
    for (const file of files) {
      const filePath = path.join(imgDir, file);
      const remotePath = `parking_lots/images/${file}`;
      await b2.uploadImage(filePath, remotePath);
    }
    console.log(`📸 已上傳 ${files.length} 張圖片`);
  } else {
    console.log('📂 data/img/ 不存在，跳過圖片上傳');
  }

  // 6. 輸出 B2 存取入口
  console.log('\n🌐 B2 資料存取入口 (提供 Flutter 使用):');
  console.log(`   JSON: ${b2.getPublicUrl('parking_lots/data.json')}`);
  console.log(`   Schema: ${b2.getPublicUrl('parking_lots/schema.json')}`);
}

// ---------- Main ----------
async function main() {
  try {
    const b2 = new B2Client(config.b2);
    await b2.authorize();
    await b2.getOrCreateBucket();
    await deployParkingLots(b2);
    console.log('\n🎉 全部部屬完成！');
  } catch (err) {
    console.error('❌ 部屬失敗:', err.message);
    process.exit(1);
  } finally {
    db.end();
  }
}

main();
