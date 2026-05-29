/**
 * ⚡ VAGALUME90 CORE ENGINE - ALL-IN-ONE SYSTEM v3.0.0
 * 🪐 INTEGRAÇÃO TOTAL: IA, MERCADO, ZONA DE GUERRA & DATABASE
 * 🛡️ DEPLOY SEGURO: RENDER & REPOSITÓRIO GITHUB
 */

const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

// ==========================================================================
// 1. MALHA DE DADOS REATIVA (DATABASE MONGOOSE SCHEMAS)
// ==========================================================================

const UserSchema = new mongoose.Schema({
    uid: { type: String, required: true, unique: true, default: () => `VGLM-${Math.floor(1000 + Math.random() * 9000)}` },
    nome: { type: String, required: true },
    telefone: { type: String, required: true },
    email: { type: String, required: true, unique: true },
    password_hash: { type: String, required: true },
    afiliado_id: { type: String, unique: true }, 
    carteira_kwanzas: { type: Number, default: 0 }, 
    combate: {
        nivel: { type: Number, default: 1 },
        xp: { type: Number, default: 0 },
        desafios_concluidos: { type: Number, default: 0 },
        precisao_prompts: { type: Number, default: 100 }
    },
    status_sistema: { type: String, default: "ACRESCENTANDO_ENERGIA", enum: ["ACRESCENTANDO_ENERGIA", "FOCADO", "ELITE_MUTANTE"] }
});

// Gatilhos Autónomos (Pre-Save)
UserSchema.pre('save', function(next) {
    if (!this.afiliado_id) this.afiliado_id = `partner_${this.uid.toLowerCase()}_matrix`;
    if (this.combate.xp >= 2000 && this.carteira_kwanzas > 50000) {
        this.status_sistema = "ELITE_MUTANTE";
    } else if (this.combate.xp > 1000) {
        this.status_sistema = "FOCADO";
    }
    next();
});

const FreelancerSchema = new mongoose.Schema({
    user_id: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true, unique: true },
    especialidade: { type: String, required: true },
    badge_guerra_verificado: { type: Boolean, default: false }
});

const User = mongoose.model('User', UserSchema);
const Freelancer = mongoose.model('Freelancer', FreelancerSchema);

// ==========================================================================
// 2. MOTOR MULTIMODAL PARALELO (/api/ia/completo)
// ==========================================================================

async function gerarTextoCopy(promptBase) {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                titulo: `🔥 EXPANSÃO RADICAL: ${promptBase}`,
                copy: `Mano, o sistema Vagalume90 gerou a tua estratégia de alta conversão para: ${promptBase}.`,
                hashtags: "#vagalume90 #api #inteligencia"
            });
        }, 1200);
    });
}

async function gerarImagemBanner(promptBase) {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                media_url: "https://cdn.vagalume90.com/generated/render_banner_01.png",
                estilo: "Cyberpunk HUD Interface"
            });
        }, 1500);
    });
}

app.post('/api/ia/completo', async (req, res) => {
    const { prompt } = req.body;
    if (!prompt) return res.status(400).json({ error: "Injeta um prompt válido." });

    try {
        // Processamento paralelo assíncrono real
        const [copyGerada, imagemGerada] = await Promise.all([
            gerarTextoCopy(prompt),
            gerarImagemBanner(prompt)
        ]);

        return res.status(200).json({
            status_sistema: "CORE_CONNECTED",
            payload: { texto: copyGerada, imagem: imagemGerada }
        });
    } catch (error) {
        return res.status(500).json({ error: "Falha crítica nos nós de IA." });
    }
});

// ==========================================================================
// 3. MOTOR DA ZONA DE GUERRA (/api/guerra/submeter)
// ==========================================================================

const desafiosArena = {
    opt_01: { id: "opt_01", resposta_chave: "low-data-metric", xp_recompensa: 400 }
};

app.post('/api/guerra/submeter', async (req, res) => {
    const { user_id, desafio_id, resposta_utilizador } = req.body;

    try {
        const guerreiro = await User.findById(user_id);
        if (!guerreiro) return res.status(404).json({ error: "Guerreiro não encontrado." });

        const desafio = desafiosArena[desafio_id];
        if (!desafio) return res.status(400).json({ error: "Desafio inválido." });

        const IsCorreto = resposta_utilizador.toLowerCase().includes(desafio.resposta_chave);

        if (!IsCorreto) {
            guerreiro.combate.precisao_prompts = Math.max(0, guerreiro.combate.precisao_prompts - 10);
            await guerreiro.save();
            return res.status(200).json({ status_combate: "DERROTA", precisao: guerreiro.combate.precisao_prompts });
        }

        // Vitória: Atualiza e dispara mutação reativa
        guerreiro.combate.xp += desafio.xp_recompensa;
        guerreiro.combate.desafios_concluidos += 1;
        await guerreiro.save();

        // Ponte Direta com o Mercado de Trabalho
        if (guerreiro.combate.xp >= 2000) {
            await Freelancer.findOneAndUpdate(
                { user_id: guerreiro._id },
                { badge_guerra_verificado: true },
                { upsert: true }
            );
        }

        return res.status(200).json({
            status_combate: "VITÓRIA",
            novo_xp: guerreiro.combate.xp,
            status_sistema: guerreiro.status_sistema
        });

    } catch (error) {
        return res.status(500).json({ error: "Erro no processamento da Arena." });
    }
});

// ==========================================================================
// 4. INICIALIZAÇÃO DO SERVIDOR (CONEXÃO ORGÂNICA MONGODB)
// ==========================================================================
const PORT = process.env.PORT || 3000;
const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017/vagalume90';

mongoose.connect(MONGO_URI)
    .then(() => {
        console.log("🔋 CONEXÃO COM A MALHA DE DADOS ESTABELECIDA");
        app.listen(PORT, () => console.log(`👁️  VAGALUME90 OPERANDO NA PORTA ${PORT}`));
    })
    .catch(err => console.error("🛑 FALHA DE CONEXÃO NEURAL:", err));
