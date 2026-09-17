import fs from "node:fs/promises";
import path from "node:path";

import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const projectRoot = path.resolve(import.meta.dirname, "..");
const sampleDir = path.join(projectRoot, "samples");
const outputDir = path.join(projectRoot, "outputs", "twr-import-samples");
await fs.mkdir(sampleDir, { recursive: true });
await fs.mkdir(outputDir, { recursive: true });

const employeesCsv = [
  "Matrícula,Nome,Email,Cargo,Base,Nível,Admissão,Ativo",
  "IMP-0001,Ana Paula Ribeiro,ana.ribeiro@example.com,FAM-01-R01,Curitiba,pleno,2026-01-12,sim",
  "IMP-0002,Carlos Henrique Lima,carlos.lima@example.com,FAM-01-R02,São Paulo,sênior,15/02/2025,sim",
].join("\n");
const qualificationsCsv = [
  "Matrícula,Código qualificação,Emitida em,Vence em,Provedor,Identificador externo",
  "SYN-00001,QLF-001,2026-01-10,2027-01-10,Centro de Treinamento Demo,CERT-DEMO-001",
  "SYN-00002,QLF-002,10/02/2026,10/02/2027,Centro de Treinamento Demo,CERT-DEMO-002",
].join("\n");
const invalidEmployeesCsv = [
  "Matrícula,Nome,Email,Cargo,Base,Nível,Admissão,Ativo",
  "IMP-ERRO,Pessoa com erro,pessoa@example.com,CARGO-INEXISTENTE,Curitiba,pleno,31/02/2026,sim",
].join("\n");

for (const [filename, csvText] of [
  ["employees.csv", employeesCsv],
  ["employee_qualifications.csv", qualificationsCsv],
  ["employees-invalid.csv", invalidEmployeesCsv],
]) {
  const workbook = await Workbook.fromCSV(csvText, { sheetName: "Importação" });
  const check = await workbook.inspect({
    kind: "table",
    range: "Importação!A1:J5",
    include: "values,formulas",
    tableMaxRows: 5,
    tableMaxCols: 10,
  });
  if (!check.ndjson.includes("Importação")) throw new Error(`Falha ao validar ${filename}`);
  await fs.writeFile(path.join(sampleDir, filename), `\uFEFF${csvText}\n`, "utf8");
}

function styleImportSheet(sheet, usedRange, widths) {
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(1);
  usedRange.format.font = { name: "Aptos", size: 10, color: "#25212A" };
  sheet.getRangeByIndexes(0, 0, 1, widths.length).format = {
    fill: "#6C0775",
    font: { name: "Aptos Display", size: 10, bold: true, color: "#FFFFFF" },
    rowHeight: 28,
    verticalAlignment: "center",
  };
  widths.forEach((width, index) => {
    sheet.getRangeByIndexes(0, index, usedRange.rowCount, 1).format.columnWidth = width;
  });
  usedRange.format.borders = {
    insideHorizontal: { style: "thin", color: "#DDD7E0" },
    bottom: { style: "thin", color: "#B9AFBD" },
  };
  usedRange.format.wrapText = false;
}

async function saveWorkbook(workbook, filename, previewName, sheetName, range) {
  const errors = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 50 },
    summary: "final formula error scan",
  });
  if (/"matchCount":\s*[1-9]/.test(errors.ndjson)) throw new Error(`${filename} contém erro`);
  const preview = await workbook.render({ sheetName, range, scale: 1.2, format: "png" });
  await fs.writeFile(
    path.join(outputDir, previewName),
    new Uint8Array(await preview.arrayBuffer()),
  );
  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(path.join(outputDir, filename));
  await output.save(path.join(sampleDir, filename));
  await fs.rm(path.join(outputDir, `${filename}.inspect.ndjson`), { force: true });
  await fs.rm(path.join(sampleDir, `${filename}.inspect.ndjson`), { force: true });
}

const operations = Workbook.create();
const operationsSheet = operations.worksheets.add("Operações");
operationsSheet.getRange("A1:O3").values = [
  ["Código operação", "Nome operação", "Cliente", "Base", "Início", "Fim", "Prazo mobilização", "Status", "Orçamento reais", "Código cargo", "Quantidade", "Turno", "Prioridade", "Qualificação obrigatória", "Permite treinamento"],
  ["OPS-IMP-01", "Parada Industrial Demonstrativa", "Cliente Demonstração", "Curitiba", new Date("2026-11-10T08:00:00Z"), new Date("2026-12-15T18:00:00Z"), new Date("2026-11-03T18:00:00Z"), "planning", 180000, "FAM-01-R01", 8, "day", 10, "QLF-001", "sim"],
  ["OPS-IMP-01", "Parada Industrial Demonstrativa", "Cliente Demonstração", "Curitiba", new Date("2026-11-10T08:00:00Z"), new Date("2026-12-15T18:00:00Z"), new Date("2026-11-03T18:00:00Z"), "planning", 180000, "FAM-01-R02", 3, "day", 20, "QLF-002", "sim"],
];
operationsSheet.getRange("E2:G3").format.numberFormat = "yyyy-mm-dd hh:mm";
operationsSheet.getRange("I2:I3").format.numberFormat = 'R$ #,##0.00';
styleImportSheet(operationsSheet, operationsSheet.getRange("A1:O3"), [17, 30, 24, 15, 20, 20, 22, 13, 18, 16, 12, 12, 12, 24, 18]);
await saveWorkbook(operations, "operations.xlsx", "operations-preview.png", "Operações", "A1:O3");

const training = Workbook.create();
const trainingSheet = training.worksheets.add("Treinamentos");
trainingSheet.getRange("A1:F3").values = [
  ["Código treinamento", "Treinamento", "Código qualificação", "Duração minutos", "Custo reais", "Ativo"],
  ["TRN-IMP-01", "NR-35 Trabalho em Altura — demonstração", "QLF-001", 480, 450, "sim"],
  ["TRN-IMP-02", "NR-33 Espaço Confinado — demonstração", "QLF-002", 960, 780, "sim"],
];
trainingSheet.getRange("D2:D3").format.numberFormat = "#,##0";
trainingSheet.getRange("E2:E3").format.numberFormat = 'R$ #,##0.00';
styleImportSheet(trainingSheet, trainingSheet.getRange("A1:F3"), [20, 42, 22, 18, 16, 12]);
await saveWorkbook(training, "training_catalog.xlsx", "training-preview.png", "Treinamentos", "A1:F3");

process.stdout.write("Amostras CSV/XLSX criadas e verificadas.\n");
