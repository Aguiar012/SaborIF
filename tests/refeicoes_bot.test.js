import assert from "node:assert/strict";
import test from "node:test";

import {
    detectarRefeicao,
    obterRefeicao,
} from "../whatsapp/bot/refeicoes.js";


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
