/**
 * ⚡ VAGALUME90 CORE ENGINE — ALL-IN-ONE SYSTEM
 * 🪐 CORE CENTRAL DO ECOSSISTEMA VG90
 *
 * Responsabilidades:
 * - Identidade única VG90
 * - Login / registo
 * - MongoDB
 * - IA multimodal
 * - Arena / Guerra
 * - Mercado
 *
 * Deploy:
 * - Render
 * - GitHub
 *
 * Variáveis necessárias:
 * - MONGO_URI
 * - PORT (fornecida pelo Render)
 * - N8N_WEBHOOK_URL (opcional)
 */

const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
const crypto = require('crypto');

require('dotenv').config();

const app = express();

app.use(cors());
app.use(express.json());


// ==========================================================================
// 1. CONFIGURAÇÃO
// ==========================================================================

const PORT = process.env.PORT || 3000;

const MONGO_URI = process.env.MONGO_URI;

const N8N_WEBHOOK_URL = process.env.N8N_WEBHOOK_URL || '';

if (!MONGO_URI) {
    console.error('🛑 MONGO_URI não configurada.');
    process.exit(1);
}


// ==========================================================================
// 2. UTILITÁRIOS
// ==========================================================================

function hashPassword(password) {
    return crypto
        .createHash('sha256')
        .update(password)
        .digest('hex');
}


function gerarUID() {
    return `VGLM-${Math.floor(1000 + Math.random() * 9000)}`;
}


// ==========================================================================
// 3. IDENTIDADE CENTRAL VG90
// ==========================================================================

const UserSchema = new mongoose.Schema(
    {
        uid: {
            type: String,
            required: true,
            unique: true,
            index: true,
            default: gerarUID
        },

        nome: {
            type: String,
            required: true,
            trim: true
        },

        telefone: {
            type: String,
            required: true,
            trim: true
        },

        email: {
            type: String,
            required: true,
            unique: true,
            index: true,
            lowercase: true,
            trim: true
        },

        password_hash: {
            type: String,
            required: true
        },

        afiliado_id: {
            type: String,
            unique: true,
            sparse: true
        },

        carteira_kwanzas: {
            type: Number,
            default: 0
        },

        combate: {
            nivel: {
                type: Number,
                default: 1
            },

            xp: {
                type: Number,
                default: 0
            },

            desafios_concluidos: {
                type: Number,
                default: 0
            },

            precisao_prompts: {
                type: Number,
                default: 100
            }
        },

        status_sistema: {
            type: String,

            default: 'ACRESCENTANDO_ENERGIA',

            enum: [
                'ACRESCENTANDO_ENERGIA',
                'FOCADO',
                'ELITE_MUTANTE'
            ]
        },

        criado_em: {
            type: Date,
            default: Date.now
        },

        ultimo_login: {
            type: Date,
            default: null
        }
    }
);


// ==========================================================================
// 4. GATILHOS DA IDENTIDADE
// ==========================================================================

UserSchema.pre('save', function(next) {

    if (!this.afiliado_id) {
        this.afiliado_id =
            `partner_${this.uid.toLowerCase()}_matrix`;
    }

    if (
        this.combate.xp >= 2000 &&
        this.carteira_kwanzas > 50000
    ) {
        this.status_sistema = 'ELITE_MUTANTE';

    } else if (this.combate.xp > 1000) {

        this.status_sistema = 'FOCADO';

    } else {

        this.status_sistema = 'ACRESCENTANDO_ENERGIA';
    }

    next();
});


const User = mongoose.model('User', UserSchema);


// ==========================================================================
// 5. FREELANCER / MERCADO DE TALENTOS
// ==========================================================================

const FreelancerSchema = new mongoose.Schema({

    user_id: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true,
        unique: true
    },

    especialidade: {
        type: String,
        default: 'Programação'
    },

    badge_guerra_verificado: {
        type: Boolean,
        default: false
    },

    criado_em: {
        type: Date,
        default: Date.now
    }
});


const Freelancer =
    mongoose.model('Freelancer', FreelancerSchema);


// ==========================================================================
// 6. HEALTH CHECK
// ==========================================================================

app.get('/health', async (req, res) => {

    const mongoEstado =
        mongoose.connection.readyState === 1;

    res.json({

        status: 'ok',

        project: 'Vagalume90 Core',

        version: '3.1.0',

        core: 'online',

        database: mongoEstado
            ? 'connected'
            : 'disconnected',

        identity: 'enabled',

        modules: {
            identity: true,
            ai: true,
            arena: true,
            market: true
        }

    });

});


// ==========================================================================
// 7. STATUS DO CORE
// ==========================================================================

app.get('/', async (req, res) => {

    res.json({

        system: 'VAGALUME90 CORE',

        status: 'ONLINE',

        version: '3.1.0',

        identity: true,

        database:
            mongoose.connection.readyState === 1
                ? 'CONNECTED'
                : 'DISCONNECTED',

        message:
            'O Core central do ecossistema VG90 está operacional.'

    });

});


// ==========================================================================
// 8. REGISTO — IDENTIDADE ÚNICA VG90
// ==========================================================================

app.post('/api/auth/register', async (req, res) => {

    try {

        const {
            nome,
            telefone,
            email,
            password
        } = req.body;


        if (
            !nome ||
            !telefone ||
            !email ||
            !password
        ) {

            return res.status(400).json({

                success: false,

                error:
                    'Nome, telefone, email e senha são obrigatórios.'

            });

        }


        if (password.length < 6) {

            return res.status(400).json({

                success: false,

                error:
                    'A senha deve ter pelo menos 6 caracteres.'

            });

        }


        const emailNormalizado =
            email.trim().toLowerCase();


        const existente =
            await User.findOne({
                email: emailNormalizado
            });


        if (existente) {

            return res.status(409).json({

                success: false,

                error:
                    'Este email já possui uma identidade VG90.',

                uid: existente.uid

            });

        }


        const utilizador =
            new User({

                nome: nome.trim(),

                telefone: telefone.trim(),

                email: emailNormalizado,

                password_hash:
                    hashPassword(password)

            });


        await utilizador.save();


        console.log(
            `👤 Nova identidade criada: ${utilizador.uid}`
        );


        return res.status(201).json({

            success: true,

            message:
                'Identidade VG90 criada com sucesso.',

            identity: {

                uid: utilizador.uid,

                nome: utilizador.nome,

                telefone: utilizador.telefone,

                email: utilizador.email,

                afiliado_id:
                    utilizador.afiliado_id,

                carteira_kwanzas:
                    utilizador.carteira_kwanzas,

                combate:
                    utilizador.combate,

                status_sistema:
                    utilizador.status_sistema

            }

        });

    } catch (error) {

        console.error(
            '🛑 Erro no registo:',
            error
        );


        return res.status(500).json({

            success: false,

            error:
                'Não foi possível criar a identidade VG90.'

        });

    }

});


// ==========================================================================
// 9. LOGIN — PORTA ÚNICA DO ECOSSISTEMA
// ==========================================================================

app.post('/api/auth/login', async (req, res) => {

    try {

        const {
            email,
            password
        } = req.body;


        if (!email || !password) {

            return res.status(400).json({

                success: false,

                error:
                    'Email e senha são obrigatórios.'

            });

        }


        const emailNormalizado =
            email.trim().toLowerCase();


        const utilizador =
            await User.findOne({
                email: emailNormalizado
            });


        if (!utilizador) {

            return res.status(401).json({

                success: false,

                error:
                    'Credenciais inválidas.'

            });

        }


        const passwordHash =
            hashPassword(password);


        if (
            utilizador.password_hash !==
            passwordHash
        ) {

            return res.status(401).json({

                success: false,

                error:
                    'Credenciais inválidas.'

            });

        }


        utilizador.ultimo_login =
            new Date();


        await utilizador.save();


        console.log(
            `🔐 Login autorizado: ${utilizador.uid}`
        );


        return res.status(200).json({

            success: true,

            message:
                'Entrada autorizada no ecossistema VG90.',

            identity: {

                uid: utilizador.uid,

                nome: utilizador.nome,

                telefone: utilizador.telefone,

                email: utilizador.email,

                afiliado_id:
                    utilizador.afiliado_id,

                carteira_kwanzas:
                    utilizador.carteira_kwanzas,

                combate:
                    utilizador.combate,

                status_sistema:
                    utilizador.status_sistema,

                ultimo_login:
                    utilizador.ultimo_login

            }

        });

    } catch (error) {

        console.error(
            '🛑 Erro no login:',
            error
        );


        return res.status(500).json({

            success: false,

            error:
                'Falha no sistema de autenticação.'

        });

    }

});


// ==========================================================================
// 10. CONSULTAR IDENTIDADE PELO UID
// ==========================================================================

app.get('/api/identity/:uid', async (req, res) => {

    try {

        const utilizador =
            await User.findOne({
                uid: req.params.uid
            }).lean();


        if (!utilizador) {

            return res.status(404).json({

                success: false,

                error:
                    'Identidade não encontrada.'

            });

        }


        // Nunca devolver a palavra-passe.
        delete utilizador.password_hash;


        return res.json({

            success: true,

            identity: utilizador

        });

    } catch (error) {

        console.error(
            '🛑 Erro ao consultar identidade:',
            error
        );


        return res.status(500).json({

            success: false,

            error:
                'Erro ao consultar identidade.'

        });

    }

});


// ==========================================================================
// 11. MOTOR MULTIMODAL
// ==========================================================================

async function gerarTextoCopy(promptBase) {

    return new Promise((resolve) => {

        setTimeout(() => {

            resolve({

                titulo:
                    `🔥 EXPANSÃO RADICAL: ${promptBase}`,

                copy:
                    `O sistema Vagalume90 gerou uma estratégia para: ${promptBase}.`,

                hashtags:
                    '#vagalume90 #api #inteligencia'

            });

        }, 1200);

    });

}


async function gerarImagemBanner(promptBase) {

    return new Promise((resolve) => {

        setTimeout(() => {

            resolve({

                media_url:
                    'https://cdn.vagalume90.com/generated/render_banner_01.png',

                estilo:
                    'Cyberpunk HUD Interface'

            });

        }, 1500);

    });

}


app.post('/api/ia/completo', async (req, res) => {

    const {
        prompt,
        uid
    } = req.body;


    if (!prompt) {

        return res.status(400).json({

            success: false,

            error:
                'Injeta um prompt válido.'

        });

    }


    try {

        let identity = null;


        if (uid) {

            identity =
                await User.findOne({
                    uid
                }).lean();

        }


        const [
            copyGerada,
            imagemGerada
        ] = await Promise.all([

            gerarTextoCopy(prompt),

            gerarImagemBanner(prompt)

        ]);


        return res.status(200).json({

            success: true,

            status_sistema:
                'CORE_CONNECTED',

            identity: identity
                ? {
                    uid: identity.uid,
                    nome: identity.nome
                }
                : null,

            payload: {

                texto: copyGerada,

                imagem: imagemGerada

            }

        });

    } catch (error) {

        console.error(
            'Erro no motor IA:',
            error
        );


        return res.status(500).json({

            success: false,

            error:
                'Falha crítica nos nós de IA.'

        });

    }

});


// ==========================================================================
// 12. ZONA DE GUERRA / ARENA
// ==========================================================================

const desafiosArena = {

    opt_01: {

        id: 'opt_01',

        resposta_chave:
            'low-data-metric',

        xp_recompensa: 400

    }

};


app.post('/api/guerra/submeter', async (req, res) => {

    const {
        user_id,
        desafio_id,
        resposta_utilizador
    } = req.body;


    try {

        const guerreiro =
            await User.findOne({
                $or: [
                    { _id: user_id },
                    { uid: user_id }
                ]
            });


        if (!guerreiro) {

            return res.status(404).json({

                success: false,

                error:
                    'Guerreiro não encontrado.'

            });

        }


        const desafio =
            desafiosArena[desafio_id];


        if (!desafio) {

            return res.status(400).json({

                success: false,

                error:
                    'Desafio inválido.'

            });

        }


        const resposta =
            String(
                resposta_utilizador || ''
            ).toLowerCase();


        const isCorreto =
            resposta.includes(
                desafio.resposta_chave
            );


        if (!isCorreto) {

            guerreiro.combate.precisao_prompts =
                Math.max(
                    0,
                    guerreiro.combate.precisao_prompts - 10
                );


            await guerreiro.save();


            return res.status(200).json({

                success: true,

                status_combate:
                    'DERROTA',

                precisao:
                    guerreiro.combate.precisao_prompts,

                novo_xp:
                    guerreiro.combate.xp,

                status_sistema:
                    guerreiro.status_sistema

            });

        }


        guerreiro.combate.xp +=
            desafio.xp_recompensa;

        guerreiro.combate.desafios_concluidos += 1;


        await guerreiro.save();


        if (
            guerreiro.combate.xp >= 2000
        ) {

            await Freelancer.findOneAndUpdate(

                {
                    user_id:
                        guerreiro._id
                },

                {
                    badge_guerra_verificado:
                        true
                },

                {
                    upsert: true,
                    new: true
                }

            );

        }


        return res.status(200).json({

            success: true,

            status_combate:
                'VITÓRIA',

            novo_xp:
                guerreiro.combate.xp,

            status_sistema:
                guerreiro.status_sistema

        });

    } catch (error) {

        console.error(
            'Erro na Arena:',
            error
        );


        return res.status(500).json({

            success: false,

            error:
                'Erro no processamento da Arena.'

        });

    }

});


// ==========================================================================
// 13. MERCADO — REGISTAR AQUISIÇÃO
// ==========================================================================

const TransacaoSchema = new mongoose.Schema({

    transacao_id: {
        type: String,
        unique: true,
        required: true
    },

    produto_id: {
        type: String,
        required: true
    },

    produto_titulo: {
        type: String,
        required: true
    },

    comprador_id: {
        type: String,
        required: true
    },

    afiliado_cod: {
        type: String,
        default: ''
    },

    status: {
        type: String,
        default: 'AGUARDANDO PROVA'
    },

    timestamp: {
        type: Date,
        default: Date.now
    }

});


const Transacao =
    mongoose.model(
        'Transacao',
        TransacaoSchema
    );


app.post('/api/mercado/comprar', async (req, res) => {

    try {

        const {
            produto_id,
            comprador_id,
            afiliado_cod
        } = req.body;


        if (
            !produto_id ||
            !comprador_id
        ) {

            return res.status(400).json({

                success: false,

                error:
                    'produto_id e comprador_id são obrigatórios.'

            });

        }


        const transacao_id =
            `TX_${Date.now()}`;


        const novaTransacao =
            new Transacao({

                transacao_id,

                produto_id,

                produto_titulo:
                    'Produto Digital',

                comprador_id,

                afiliado_cod:
                    afiliado_cod || '',

                status:
                    'AGUARDANDO PROVA'

            });


        await novaTransacao.save();


        if (N8N_WEBHOOK_URL) {

            try {

                await fetch(
                    N8N_WEBHOOK_URL,
                    {
                        method: 'POST',

                        headers: {
                            'Content-Type':
                                'application/json'
                        },

                        body: JSON.stringify({

                            event:
                                'requisicao_aquisicao',

                            transacao_id,

                            produto_id,

                            comprador_id,

                            afiliado_cod:
                                afiliado_cod || '',

                            status:
                                'AGUARDANDO PROVA'

                        })
                    }
                );

            } catch (error) {

                console.warn(
                    '⚠️ n8n não respondeu.'
                );

            }

        }


        return res.status(200).json({

            success: true,

            transacao_id,

            status:
                'AGUARDANDO PROVA'

        });

    } catch (error) {

        console.error(
            'Erro no Mercado:',
            error
        );


        return res.status(500).json({

            success: false,

            error:
                'Erro ao processar aquisição.'

        });

    }

});


// ==========================================================================
// 14. LISTAR INFORMAÇÃO PÚBLICA DA IDENTIDADE
// ==========================================================================

app.get('/api/identity/:uid/public', async (req, res) => {

    try {

        const utilizador =
            await User.findOne({
                uid: req.params.uid
            })
            .select(
                'uid nome afiliado_id status_sistema combate.nivel combate.xp'
            )
            .lean();


        if (!utilizador) {

            return res.status(404).json({

                success: false,

                error:
                    'Identidade não encontrada.'

            });

        }


        return res.json({

            success: true,

            identity: utilizador

        });

    } catch (error) {

        return res.status(500).json({

            success: false,

            error:
                'Erro ao consultar identidade.'

        });

    }

});


// ==========================================================================
// 15. CONEXÃO MONGODB + ARRANQUE
// ==========================================================================

mongoose
    .connect(MONGO_URI)
    .then(() => {

        console.log(
            '🔋 CONEXÃO COM A MALHA DE DADOS ESTABELECIDA'
        );

        console.log(
            '🧬 IDENTIDADE CENTRAL VG90 ATIVA'
        );

        app.listen(
            PORT,
            '0.0.0.0',
            () => {

                console.log(
                    `👁️ VAGALUME90 CORE OPERANDO NA PORTA ${PORT}`
                );

            }
        );

    })
    .catch((err) => {

        console.error(
            '🛑 FALHA DE CONEXÃO NEURAL:',
            err
        );

        process.exit(1);

    });
