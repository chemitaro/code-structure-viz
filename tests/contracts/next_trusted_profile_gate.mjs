import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import ts from "typescript";

const here = dirname(new URL(import.meta.url).pathname);
const fixtureRoot = resolve(here, "../fixtures/next_trusted_profile");
const fixtureNames = ["jsx-runtime.d.ts", "lib.d.ts", "next-dynamic.d.ts", "react.d.ts"];
const fixturePaths = fixtureNames.map((name) => join(fixtureRoot, name));
const expectedPath = join(fixtureRoot, "expected_inventory.json");

function canonicalize(value) {
  if (typeof value === "string") return value.normalize("NFC");
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .map(([key, item]) => [key.normalize("NFC"), canonicalize(item)])
        .sort(([left], [right]) => (left < right ? -1 : left > right ? 1 : 0)),
    );
  }
  return value;
}

function canonicalJson(value) {
  return JSON.stringify(canonicalize(value));
}

function sha256(value) {
  return createHash("sha256").update(value, "utf8").digest("hex");
}

function declarationKind(symbol) {
  const declaration = symbol.declarations?.[0];
  if (!declaration) throw new Error(`missing declaration for ${symbol.getName()}`);
  if (ts.isFunctionDeclaration(declaration) || ts.isMethodSignature(declaration)) {
    return ts.isMethodSignature(declaration) ? "method" : "function";
  }
  if (ts.isClassDeclaration(declaration)) return "class";
  if (ts.isInterfaceDeclaration(declaration)) return "interface";
  if (ts.isModuleDeclaration(declaration)) return "namespace";
  if (ts.isVariableDeclaration(declaration)) return "variable";
  if (ts.isTypeAliasDeclaration(declaration)) return "type";
  throw new Error(`unsupported declaration kind for ${symbol.getName()}`);
}

function declarationFile(symbol) {
  const declaration = symbol.declarations?.[0];
  if (!declaration) throw new Error(`missing declaration for ${symbol.getName()}`);
  const name = relative(fixtureRoot, declaration.getSourceFile().fileName);
  if (!fixtureNames.includes(name)) throw new Error(`declaration escaped fixture root: ${name}`);
  return name;
}

function symbolRow(checker, sourceKind, sourceName, exportPath, symbol) {
  const declaration = symbol.declarations?.[0];
  if (!declaration) throw new Error(`missing declaration for ${sourceName}:${exportPath.join(".")}`);
  const symbolKind = declarationKind(symbol);
  const type = checker.getTypeOfSymbolAtLocation(symbol, declaration);
  const typeString = checker.typeToString(
    type,
    declaration,
    ts.TypeFormatFlags.NoTruncation | ts.TypeFormatFlags.UseFullyQualifiedType,
  );
  const identity = {
    source_kind: sourceKind,
    source_name: sourceName,
    export_path: exportPath,
    symbol_kind: symbolKind,
    type_string: typeString,
  };
  return {
    ...identity,
    declaration_file: declarationFile(symbol),
    signature_digest: sha256(canonicalJson(identity)),
  };
}

function moduleSymbol(checker, name) {
  const module = checker
    .getAmbientModules()
    .find((candidate) => candidate.name === JSON.stringify(name));
  if (!module) throw new Error(`missing ambient module ${name}`);
  return module;
}

function exportSymbol(checker, module, name) {
  const symbol = checker.getExportsOfModule(module).find((candidate) => candidate.getName() === name);
  if (!symbol) throw new Error(`missing export ${module.name}:${name}`);
  return symbol;
}

function globalSymbol(checker, name) {
  const symbol = checker.resolveName(
    name,
    undefined,
    ts.SymbolFlags.Type | ts.SymbolFlags.Namespace,
    false,
  );
  if (!symbol) throw new Error(`missing global ${name}`);
  return symbol;
}

function deriveInventory(program) {
  const checker = program.getTypeChecker();
  const rows = [];
  for (const [moduleName, exports] of [
    ["next/dynamic", ["default"]],
    ["react", ["Component", "createElement", "forwardRef", "lazy", "memo"]],
    ["react/jsx-runtime", ["Fragment", "jsx", "jsxs"]],
  ]) {
    const module = moduleSymbol(checker, moduleName);
    for (const name of exports) rows.push(symbolRow(checker, "module", moduleName, [name], exportSymbol(checker, module, name)));
  }

  for (const [globalName, members] of [
    ["Array", ["flatMap", "map"]],
    ["JSX", ["Element"]],
    ["ReadonlyArray", ["flatMap", "map"]],
  ]) {
    const global = globalSymbol(checker, globalName);
    const memberSymbols =
      globalName === "JSX"
        ? checker.getExportsOfModule(global)
        : checker.getPropertiesOfType(checker.getDeclaredTypeOfSymbol(global));
    const memberMap = new Map(memberSymbols.map((member) => [member.getName(), member]));
    for (const name of members) {
      const member = memberMap.get(name);
      if (!member) throw new Error(`missing global member ${globalName}.${name}`);
      rows.push(symbolRow(checker, "global", globalName, [name], member));
    }
  }
  return rows.sort((left, right) =>
    Buffer.from(canonicalJson(left), "utf8").compare(Buffer.from(canonicalJson(right), "utf8")),
  );
}

const compilerOptions = {
  noEmit: true,
  noLib: true,
  strict: true,
  target: ts.ScriptTarget.ES2022,
  module: ts.ModuleKind.ESNext,
  moduleResolution: ts.ModuleResolutionKind.Bundler,
};
const program = ts.createProgram(fixturePaths, compilerOptions);
const diagnostics = [...program.getSyntacticDiagnostics(), ...program.getSemanticDiagnostics()];
if (diagnostics.length !== 0) {
  const details = ts.formatDiagnosticsWithColorAndContext(diagnostics, {
    getCanonicalFileName: (fileName) => fileName,
    getCurrentDirectory: () => fixtureRoot,
    getNewLine: () => "\n",
  });
  throw new Error(`trusted profile diagnostics are not empty:\n${details}`);
}

const inventory = deriveInventory(program);
let expected;
try {
  expected = JSON.parse(readFileSync(expectedPath, "utf8"));
} catch (error) {
  if (process.argv.includes("--print") && error?.code === "ENOENT") {
    process.stdout.write(`${JSON.stringify(inventory, null, 2)}\n`);
    process.exit(0);
  }
  throw error;
}
if (canonicalJson(inventory) !== canonicalJson(expected)) {
  if (process.argv.includes("--print")) {
    process.stdout.write(`${JSON.stringify(inventory, null, 2)}\n`);
  }
  throw new Error("derived trusted symbol inventory differs from checked-in expected inventory");
}
process.stdout.write(`trusted-profile: TypeScript ${ts.version}; diagnostics=0; symbols=${inventory.length}\n`);
