// Apenas leitura: falhas de uma nova tentativa não apagam tickets confirmados.
export function classificarMotivo(motivoBruto = "") {
    const completo = String(motivoBruto || "");
    const idx = completo.indexOf(":");
    const detalhe = idx >= 0 ? completo.slice(idx + 1).trim() : completo;
    const texto = completo.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
    let tipo = "OUTRO";
    if (/^(cancelado_diretamente|cancelamento_email)/.test(texto)) tipo = "CANCELADO";
    else if (/^(nao_pediu|nao pediu):/.test(texto)) tipo = "NAO_PEDIU";
    else if (texto.startsWith("pediu_ok:")) tipo = "PEDIU_OK";
    else {
        // O cabeçalho "não foi gerado" também aparece quando já existe ticket.
        const motivo = texto.replace(/^erro_pedido:\s*/, "")
            .split(/devido ao problema\s*:\s*/).at(-1).trim().replace(/^×\s*/, "");
        const confirmado = /^(?:ticket\s+)?(?:gerado anteriormente|ja (?:foi )?(?:pedido|solicitado|gerado)|gerado(?: com sucesso)?)[.!\s]*$/.test(motivo);
        if (confirmado) tipo = "PEDIU_OK";
        else if (texto.startsWith("erro_pedido:")) tipo = "ERRO_PEDIDO";
    }
    return { tipo, detalhe, bruto: completo };
}

export function consolidarPedidos(pedidos) {
    // A consulta deve vir em id DESC dentro de cada dia. Cada grupo é independente.
    const grupos = new Map();
    for (const pedido of pedidos) {
        const data = pedido.dia_pedido instanceof Date
            ? `${pedido.dia_pedido.getFullYear()}-${String(pedido.dia_pedido.getMonth() + 1).padStart(2, "0")}-${String(pedido.dia_pedido.getDate()).padStart(2, "0")}`
            : String(pedido.dia_pedido).slice(0, 10);
        const chave = `${pedido.aluno_id ?? ""}/${pedido.refeicao || "almoco"}/${data}`;
        if (!grupos.has(chave)) grupos.set(chave, []);
        grupos.get(chave).push(pedido);
    }
    return [...grupos.values()].map(tentativas =>
        tentativas.find(p => ["PEDIU_OK", "CANCELADO"].includes(classificarMotivo(p.motivo).tipo))
        || tentativas[0]
    );
}
