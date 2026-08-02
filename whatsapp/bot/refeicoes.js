const REFEICOES = {
    almoco: { nome: "almoco", titulo: "Almoço", codigoSica: "1" },
    jantar: { nome: "jantar", titulo: "Jantar", codigoSica: "2" },
};

function semAcentos(valor = "") {
    return String(valor)
        .trim()
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "");
}

export function obterRefeicao(valor = "almoco") {
    const texto = semAcentos(valor);
    if (["1", "almoco"].includes(texto)) return REFEICOES.almoco;
    if (["2", "janta", "jantar"].includes(texto)) return REFEICOES.jantar;
    throw new Error(`Refeicao invalida: ${valor}`);
}

export function detectarRefeicao(texto, padrao = "almoco") {
    const normalizado = semAcentos(texto);
    if (/\b(janta|jantar)\b/.test(normalizado)) return REFEICOES.jantar;
    if (/\balmoco\b/.test(normalizado)) return REFEICOES.almoco;
    return obterRefeicao(padrao);
}

export function criarMensagemConfirmacaoTroca(valor) {
    const refeicao = obterRefeicao(valor);
    const avisoJantar = refeicao.nome === "jantar"
        ? "⚠️ O jantar está disponível somente para alguns alunos, conforme autorização da CAE. Confirme apenas se você faz parte desse grupo.\n\n"
        : "";

    return `${avisoJantar}Trocar sua refeição para *${refeicao.titulo}*?\n\nSeus dias escolhidos e pratos bloqueados serão mantidos.`;
}

export function interpretarConfirmacaoTroca(texto) {
    const normalizado = semAcentos(texto)
        .replace(/[^a-z0-9_]+/g, " ")
        .trim();

    if (
        normalizado === "confirmar_troca_refeicao" ||
        /^(sim|s|ok)(\s|$)/.test(normalizado)
    ) return "SIM";

    if (
        normalizado === "cancelar_troca_refeicao" ||
        /^(nao|n)(\s|$)/.test(normalizado)
    ) return "NAO";

    return "INCONCLUSIVO";
}

export function analisarComandoCancelamento(texto) {
    const normalizado = semAcentos(texto);
    const mencionouRefeicao = /\b(almoco|janta|jantar)\b/.test(normalizado);
    const comandoSemRefeicao = normalizado
        .replace(/\b(almoco|janta|jantar)\b/g, "")
        .replace(/\s+/g, " ")
        .trim();

    return {
        refeicao: detectarRefeicao(normalizado).nome,
        mencionouRefeicao,
        comandoSemRefeicao,
    };
}
