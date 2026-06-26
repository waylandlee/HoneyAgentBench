fetch('http://127.0.0.1:3000/').then(async r => {
  console.log('status=' + r.status);
  const t = await r.text();
  console.log(t.slice(0, 700));
}).catch(e => {
  console.error(e);
  process.exit(1);
});
