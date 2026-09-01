import assert from "node:assert/strict";
import test from "node:test";

import {
    analisarComandoCancelamento,
    criarMensagemConfirmacaoTroca,
    detectarRefeicao,
    interpretarConfirmacao,
    interpretarConfirmacaoTroca,
    obterRefeicao,
} from "../whatsapp/bot/refeicoes.js";
import { gerarImagemEmailCancelamento } from "../whatsapp/bot/renderizar_email.js";


test("reconhece almoco com acento e codigo", () => {
    assert.equal(obterRefeicao("almoço").codigoSica, "1");
    assert.equal(obterRefeicao(1).nome, "almoco");
});

test("reconhece jantar, janta e codigo", () => {
    assert.equal(obterRefeicao("jantar").codigoSica, "2");
    assert.equal(obterRefeicao("janta").nome, "jantar");
    assert.equal(obterRefeicao(2).nome, "jantar");
});

test("detecta a refeicao mencionada em uma frase", () => {
    assert.equal(detectarRefeicao("quero cancelar a janta").nome, "jantar");
    assert.equal(detectarRefeicao("alterar dias do almoço").nome, "almoco");
    assert.equal(detectarRefeicao("alterar dias").nome, "almoco");
});

test("identifica quando o cancelamento menciona uma refeicao", () => {
    const ambiguo = analisarComandoCancelamento("cancelar quarta");
    assert.equal(ambiguo.mencionouRefeicao, false);
    assert.equal(ambiguo.comandoSemRefeicao, "cancelar quarta");

    const jantar = analisarComandoCancelamento("cancelar jantar quarta");
    assert.equal(jantar.mencionouRefeicao, true);
    assert.equal(jantar.refeicao, "jantar");
    assert.equal(jantar.comandoSemRefeicao, "cancelar quarta");
});

test("avisa sobre a autorizacao da CAE antes de trocar para jantar", () => {
    const mensagem = criarMensagemConfirmacaoTroca("jantar");
    assert.match(mensagem, /autorização da CAE/);
    assert.match(mensagem, /dias escolhidos e pratos bloqueados serão mantidos/);
});

test("aceita o texto mostrado na confirmacao da troca", () => {
    assert.equal(interpretarConfirmacaoTroca("sim, trocar"), "SIM");
    assert.equal(interpretarConfirmacaoTroca("Sim, trocar"), "SIM");
    assert.equal(interpretarConfirmacaoTroca("confirmar_troca_refeicao"), "SIM");
    assert.equal(interpretarConfirmacaoTroca("não"), "NAO");
    assert.equal(interpretarConfirmacaoTroca("talvez"), "INCONCLUSIVO");
});

test("interpreta variacoes comuns de confirmacao e recusa deterministica", () => {
    assert.equal(interpretarConfirmacao("sim"), "SIM");
    assert.equal(interpretarConfirmacao("SIMMM"), "SIM");
    assert.equal(interpretarConfirmacao("1"), "SIM");
    assert.equal(interpretarConfirmacao("ok"), "SIM");
    assert.equal(interpretarConfirmacao("com certeza"), "SIM");
    assert.equal(interpretarConfirmacao("pode ser"), "SIM");
    assert.equal(interpretarConfirmacao("confirmo"), "SIM");
    assert.equal(interpretarConfirmacao("confirmar_exclusao_dados"), "SIM");
    assert.equal(interpretarConfirmacao("sim, excluir meus dados"), "SIM");
    assert.equal(interpretarConfirmacao("sim, excluir meu cadastro"), "SIM");
    assert.equal(interpretarConfirmacao("1. Sim, excluir meu cadastro"), "SIM");
    assert.equal(interpretarConfirmacao("nao"), "NAO");
    assert.equal(interpretarConfirmacao("NÃO"), "NAO");
    assert.equal(interpretarConfirmacao("2"), "NAO");
    assert.equal(interpretarConfirmacao("de jeito nenhum"), "NAO");
    assert.equal(interpretarConfirmacao("cancelar"), "NAO");
    assert.equal(interpretarConfirmacao("cancelar_abortar"), "NAO");
    assert.equal(interpretarConfirmacao("cancelar_exclusao_dados"), "NAO");
    assert.equal(interpretarConfirmacao("manter cadastro"), "NAO");
    assert.equal(interpretarConfirmacao("2. Não, manter cadastro"), "NAO");
    assert.equal(interpretarConfirmacao("invalido xyz"), "INCONCLUSIVO");
});

test("gera o preview de cancelamento de jantar", async () => {
    const imagem = await gerarImagemEmailCancelamento({
        nome: "Aluno Teste",
        prontuarioCompleto: "PT0000000",
        prontuarioNumerico: "0000000",
        diaSemana: "Segunda-Feira",
        data: "03/08",
        refeicao: "jantar",
    });

    assert.ok(Buffer.isBuffer(imagem));
    assert.ok(imagem.length > 1000);
});
