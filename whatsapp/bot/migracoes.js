import fs from "fs/promises";
import { fileURLToPath } from "url";
import pkg from "pg";

const { Client } = pkg;
const CAMINHO_MIGRACAO = fileURLToPath(
    new URL("../../migrations/001_adicionar_refeicoes.sql", import.meta.url)
);

export async function executarMigracoes(urlBanco, logger = console) {
    if (!urlBanco) {
        logger.warn("[DB] DATABASE_URL vazio; migracoes nao foram executadas.");
        return;
    }

    const sql = await fs.readFile(CAMINHO_MIGRACAO, "utf8");
    const cliente = new Client({ connectionString: urlBanco });

    try {
        await cliente.connect();
        await cliente.query(sql);
        logger.info("[DB] Estrutura de almoco e jantar pronta.");
    } finally {
        await cliente.end().catch(() => {});
    }
}
