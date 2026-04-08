const fs = require('fs');
const path = require('path');

const SKILLS_DIR = "C:\\Users\\PC\\Desktop\\skills\\skills_abril";
const DEST_DIR = path.join(process.cwd(), ".agents", "skills");

if (!fs.existsSync(DEST_DIR)){
    fs.mkdirSync(DEST_DIR, { recursive: true });
}

// Get args passed by the agent
const RELEVANCE_KEYWORDS = process.argv.slice(2).map(k => k.toLowerCase());
if (RELEVANCE_KEYWORDS.length === 0) {
    console.log("Por favor, provee keywords del stack. Ejemplo: node skill-selector.js next.js react typescript");
    process.exit(1);
}

let scored_files = [];

function scan_file(filepath, folderPath) {
    let content;
    try {
        content = fs.readFileSync(filepath, 'utf-8');
    } catch (e) { return; }
    let content_lower = content.toLowerCase();
    
    let score = 0;
    for (const keyword of RELEVANCE_KEYWORDS) {
        let regex = new RegExp(keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
        let matches = content_lower.match(regex);
        if (matches && matches.length > 0) {
            score += matches.length;
        }
    }
    if (score > 0) {
        scored_files.push({ filepath, folderPath, score });
    }
}

function walkSync(dir) {
    let files;
    try {
        files = fs.readdirSync(dir);
    } catch (e) { return; }

    for (const file of files) {
        let filepath = path.join(dir, file);
        if (filepath.includes('auditoria') || filepath.includes('OBLIGATORIAS_SIEMPRE')) continue;
        
        let stat;
        try {
            stat = fs.statSync(filepath);
        } catch (e) { continue; }

        if (stat.isDirectory()) {
            walkSync(filepath);
        } else if (file === 'SKILL.md') {
            scan_file(filepath, dir); // dir is the skill folder
        }
    }
}

console.log("Analizando la bóveda de skills con keywords: " + RELEVANCE_KEYWORDS.join(", ") + " ...");
walkSync(SKILLS_DIR);

scored_files.sort((a, b) => b.score - a.score);

// Filter highest unique skill folders
let unique_folders = new Set();
let top_skills = [];
for (let item of scored_files) {
    if (!unique_folders.has(item.folderPath)) {
        unique_folders.add(item.folderPath);
        top_skills.push(item);
        if (top_skills.length >= 10) break; // Take top 10 unique skills
    }
}

if (top_skills.length === 0) {
    console.log("No se encontraron skills relevantes para tus keywords en la bóveda.");
    process.exit(0);
}

console.log(`\nCopiando las ${top_skills.length} mejores skills a ${DEST_DIR}\n---`);
for (const item of top_skills) {
    const skillFolderName = path.basename(item.folderPath);
    const targetFolder = path.join(DEST_DIR, skillFolderName);
    
    if (!fs.existsSync(targetFolder)) {
        fs.cpSync(item.folderPath, targetFolder, { recursive: true });
        console.log(`✅ Instalada: ${skillFolderName} (Score del contexto: ${item.score})`);
    } else {
        console.log(`⏩ Omitida (ya existe localmente): ${skillFolderName}`);
    }
}
console.log("---\n¡Instalación automática completada! El agente ahora está optimizado para desarrollar en tu stack.");
