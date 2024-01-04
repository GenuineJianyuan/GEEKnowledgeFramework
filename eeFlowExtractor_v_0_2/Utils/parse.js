// parse.js
const acorn = require('c:/Users/Administrator/node_modules/acorn/dist/acorn');
// const acorn = require('c:/Users/Huawei/node_modules/acorn/dist/acorn');
const fs = require("fs");

const type = process.argv[3]
let code = ''
let comments=[]
try {
    if (type === '0') {  //从文件中读入脚本源码
        code = fs.readFileSync(process.argv[2], "utf8");
    } else {
        code = process.argv[2]
    }
    
    let ast = acorn.parse(code, {
        ecmaVersion: 2020, 
        onComment:comments
    });

    ast['raw'] = code
    ast['comments']=comments
    console.log(JSON.stringify(ast, null, 2));
} catch (error) {
    console.log(error);
}



