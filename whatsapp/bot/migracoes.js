import fs from "fs/promises";
import { fileURLToPath } from "url";
import pkg from "pg";

const { Client } = pkg;
const CAMINHOS_MIGRACAO = [
    fileURLToPath(
        new URL("../../migrations/001_adicionar_refeicoes.sql", import.meta.url)
    ),
    fileURLToPath(
        new URL("../../migrations/002_adicionar_consentimento.sql", import.meta.url)
    ),
];

export async function executarMigracoes(urlBanco, logger = console) {
    if (!urlBanco) {
        logger.warn("[DB] DATABASE_URL vazio; migracoes nao foram executadas.");
        return;
    }

    const sqls = await Promise.all(
    CAMINHOS_MIGRACAO.map(caminho => fs.readFile(caminho, "utf8"))
    );
    const cliente = new Client({ connectionString: urlBanco });

    try {
        await cliente.connect();
        for (const sql of sqls) {
            await cliente.query(sql);
        }
        logger.info("[DB] Migrações do banco concluídas.");
    } finally {
        await cliente.end().catch(() => {});
    }
}
