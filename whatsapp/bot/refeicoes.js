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
