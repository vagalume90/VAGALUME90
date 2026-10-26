/**
 * ⚡ VAGALUME90 CORE ENGINE — ALL-IN-ONE SYSTEM
 * 🪐 CORE CENTRAL DO ECOSSISTEMA VG90
 *
 * Responsabilidades:
 * - Identidade única VG90
 * - Login / registo
 * - Sessões seguras
 * - MongoDB
 * - IA multimodal
 * - Arena / Guerra
 * - Mercado
 *
 * Deploy:
 * - Render
 * - GitHub
 *
 * Variáveis:
 * - MONGO_URI
 * - PORT
 * - SESSION_SECRET
 * - CORS_ORIGIN (opcional)
 * - VG90_SERVICE_SECRET
 * - N8N_WEBHOOK_URL (opcional)
 */

require('dotenv').config();

const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
const crypto = require('crypto');
const session = require('express-session');
const MongoStore = require('connect-mongo');
const argon2 = require('argon2');
const path = require('path');

const app = express();


// ==========================================================================
// 1. CONFIGURAÇÃO
// ==========================================================================

const PORT = process.env.PORT || 3000;

const MONGO_URI = process.env.MONGO_URI;

const SESSION_SECRET =
    process.env.SESSION_SECRET || '';

const N8N_WEBHOOK_URL =
    process.env.N8N_WEBHOOK_URL || '';

const VG90_SERVICE_SECRET =
    process.env.VG90_SERVICE_SECRET || '';


// ==========================================================================
// 2. VALIDAÇÃO DAS VARIÁVEIS
// ==========================================================================

if (!MONGO_URI) {

    console.error(
        '🛑 MONGO_URI não configurada.'
    );

    process.exit(1);
}


if (
    !SESSION_SECRET ||
    SESSION_SECRET.length < 32
) {

    console.error(
        '🛑 SESSION_SECRET é obrigatória e deve ter pelo menos 32 caracteres.'
    );

    process.exit(1);
}


// ==========================================================================
// 3. CORS
// ==========================================================================

const allowedOrigins =
    (process.env.CORS_ORIGIN || '')
        .split(',')
        .map(origin => origin.trim())
        .filter(Boolean);


app.use(
    cors({

        origin: function(origin, callback) {

            /*
             * Permite chamadas sem Origin.
             * Útil para health checks e chamadas servidor-servidor.
             */

            if (!origin) {

                return callback(null, true);

            }


            if (
                allowedOrigins.length === 0 ||
                allowedOrigins.includes(origin)
            ) {

                return callback(null, true);

            }


            return callback(
                new Error(
                    'Origem não autorizada pelo CORS.'
                )
            );

        },

        credentials: true,

        methods: [
            'GET',
            'POST',
            'PUT',
            'PATCH',
            'DELETE',
            'OPTIONS'
        ],

        allowedHeaders: [
            'Content-Type',
            'X-VG90-Service-Key'
        ]

    })
);


app.use(
    express.json({
        limit: '1mb'
    })
);


// ==========================================================================
// 4. SESSÃO CENTRAL VG90
// ==========================================================================

app.set(
    'trust proxy',
    1
);


app.use(
    session({

        name:
            'vg90.sid',

        secret:
            SESSION_SECRET,

        resave:
            false,

        saveUninitialized:
            false,

        rolling:
            true,

        store:
            MongoStore.create({

                mongoUrl:
                    MONGO_URI,

                collectionName:
                    'vg90_sessions',

                ttl:
                    7 * 24 * 60 * 60

            }),

        cookie: {

            httpOnly:
                true,

            secure:
                process.env.NODE_ENV === 'production',

            sameSite:
                process.env.COOKIE_SAME_SITE ||
                'none',

            maxAge:
                7 * 24 * 60 * 60 * 1000

        }

    })
);


// ==========================================================================
// 5. AUTENTICAÇÃO INTERNA ENTRE SERVIÇOS VG90
// ==========================================================================

function verificarServicoVG90(
    req,
    res,
    next
) {

    if (!VG90_SERVICE_SECRET) {

        return res.status(503).json({

            success: false,

            error:
                'Autenticação interna não configurada.'

        });

    }


    const recebida =
        Buffer.from(
            req.get(
                'X-VG90-Service-Key'
            ) || '',
            'utf8'
        );


    const esperada =
        Buffer.from(
            VG90_SERVICE_SECRET,
            'utf8'
        );


    if (
        recebida.length !==
            esperada.length ||
        !crypto.timingSafeEqual(
            recebida,
            esperada
        )
    ) {

        return res.status(401).json({

            success: false,

            error:
                'Serviço não autorizado.'

        });

    }


    next();

}


// ==========================================================================
// 6. PROTEÇÃO DE SESSÃO
// ==========================================================================

function exigirLogin(
    req,
    res,
    next
) {

    if (
        !req.session ||
        !req.session.userId
    ) {

        return res.status(401).json({

            success: false,

            error:
                'Inicia sessão para continuar.'

        });

    }


    next();

}


// ==========================================================================
// 7. UTILITÁRIOS
// ==========================================================================

function hashSha256(
    password
) {

    return crypto
        .createHash('sha256')
        .update(password)
        .digest('hex');

}


function gerarUID() {

    return `VGLM-${crypto.randomInt(
        1000,
        10000
    )}`;

}


function identidadePublica(
    utilizador
) {

    return {

        uid:
            utilizador.uid,

        nome:
            utilizador.nome,

        telefone:
            utilizador.telefone,

        email:
            utilizador.email,

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

    };

}


// ==========================================================================
// 8. IDENTIDADE CENTRAL VG90
// ==========================================================================

const UserSchema =
    new mongoose.Schema({

        uid: {

            type:
                String,

            required:
                true,

            unique:
                true,

            index:
                true,

            default:
                gerarUID

        },


        nome: {

            type:
                String,

            required:
                true,

            trim:
                true

        },


        telefone: {

            type:
                String,

            required:
                true,

            trim:
                true

        },


        email: {

            type:
                String,

            required:
                true,

            unique:
                true,

            index:
                true,

            lowercase:
                true,

            trim:
                true

        },


        password_hash: {

            type:
                String,

            required:
                true

        },


        afiliado_id: {

            type:
                String,

            unique:
                true,

            sparse:
                true

        },


        carteira_kwanzas: {

            type:
                Number,

            default:
                0

        },


        combate: {

            nivel: {

                type:
                    Number,

                default:
                    1

            },


            xp: {

                type:
                    Number,

                default:
                    0

            },


            desafios_concluidos: {

                type:
                    Number,

                default:
                    0

            },


            precisao_prompts: {

                type:
                    Number,

                default:
                    100

            }

        },


        status_sistema: {

            type:
                String,

            default:
                'ACRESCENTANDO_ENERGIA',

            enum: [

                'ACRESCENTANDO_ENERGIA',

                'FOCADO',

                'ELITE_MUTANTE'

            ]

        },


        criado_em: {

            type:
                Date,

            default:
                Date.now

        },


        ultimo_login: {

            type:
                Date,

            default:
                null

        }

    });


// ==========================================================================
// 9. GATILHOS DA IDENTIDADE
// ==========================================================================

UserSchema.pre(
    'save',
    function(next) {

        if (!this.afiliado_id) {

            this.afiliado_id =
                `partner_${this.uid.toLowerCase()}_matrix`;

        }


        if (
            this.combate.xp >= 2000 &&
            this.carteira_kwanzas > 50000
        ) {

            this.status_sistema =
                'ELITE_MUTANTE';

        }

        else if (
            this.combate.xp > 1000
        ) {

            this.status_sistema =
                'FOCADO';

        }

        else {

            this.status_sistema =
                'ACRESCENTANDO_ENERGIA';

        }


        next();

    }
);


const User =
    mongoose.model(
        'User',
        UserSchema
    );


// ==========================================================================
// 10. FREELANCER / MERCADO DE TALENTOS
// ==========================================================================

const FreelancerSchema =
    new mongoose.Schema({

        user_id: {

            type:
                mongoose.Schema.Types.ObjectId,

            ref:
                'User',

            required:
                true,

            unique:
                true

        },


        especialidade: {

            type:
                String,

            default:
                'Programação'

        },


        badge_guerra_verificado: {

            type:
                Boolean,

            default:
                false

        },


        criado_em: {

            type:
                Date,

            default:
                Date.now

        }

    });


const Freelancer =
    mongoose.model(
        'Freelancer',
        FreelancerSchema
    );


// ==========================================================================
// 11. TRANSAÇÕES DO MERCADO
// ==========================================================================

const TransacaoSchema =
    new mongoose.Schema({

        transacao_id: {

            type:
                String,

            unique:
                true,

            required:
                true

        },


        produto_id: {

            type:
                String,

            required:
                true

        },


        produto_titulo: {

            type:
                String,

            required:
                true

        },


        comprador_id: {

            type:
                String,

            required:
                true

        },


        afiliado_cod: {

            type:
                String,

            default:
                ''

        },


        status: {

            type:
                String,

            default:
                'AGUARDANDO PROVA'

        },


        timestamp: {

            type:
                Date,

            default:
                Date.now

        }

    });


const Transacao =
    mongoose.model(
        'Transacao',
        TransacaoSchema
    );


// ==========================================================================
// 12. HEALTH CHECK
// ==========================================================================

app.get(
    '/health',
    (req, res) => {

        const mongoEstado =
            mongoose.connection.readyState === 1;


        res.json({

            status:
                'ok',

            project:
                'Vagalume90 Core',

            version:
                '3.3.0',

            core:
                'online',

            database:
                mongoEstado
                    ? 'connected'
                    : 'disconnected',

            identity:
                'enabled',

            modules: {

                identity:
                    true,

                ai:
                    true,

                arena:
                    true,

                market:
                    true

            }

        });

    }
);


// ==========================================================================
// 13. STATUS DO CORE
// ==========================================================================

app.get(
    '/',
    (req, res) => {

        // Mostra o portal visual de login e registo.
        return res.sendFile(
            path.join(__dirname, 'templates', 'index.html')
        );

    }
);


// Estado do Core separado da página visual.
app.get(
    '/api/status',
    (req, res) => {

        return res.json({

            system:
                'VAGALUME90 CORE',

            status:
                'ONLINE',

            version:
                '3.3.0',

            identity:
                true,

            database:
                mongoose.connection.readyState === 1
                    ? 'CONNECTED'
                    : 'DISCONNECTED',

            message:
                'O Core central do ecossistema VG90 está operacional.'

        });

    }
);


// ==========================================================================
// 14. REGISTO
// ==========================================================================

app.post(
    '/api/auth/register',
    async (req, res) => {

        try {

            const {

                nome,

                telefone,

                email,

                password

            } = req.body || {};


            if (
                typeof nome !== 'string' ||
                typeof telefone !== 'string' ||
                typeof email !== 'string' ||
                typeof password !== 'string' ||
                !nome.trim() ||
                !telefone.trim() ||
                !email.trim() ||
                !password
            ) {

                return res.status(400).json({

                    success:
                        false,

                    error:
                        'Nome, telefone, email e senha são obrigatórios.'

                });

            }


            // Senha mais forte:
            // mínimo 8 caracteres.

            if (
                password.length < 8
            ) {

                return res.status(400).json({

                    success:
                        false,

                    error:
                        'A senha deve ter pelo menos 8 caracteres.'

                });

            }


            const emailNormalizado =
                email
                    .trim()
                    .toLowerCase();


            const existente =
                await User.findOne({

                    email:
                        emailNormalizado

                });


            if (existente) {

                return res.status(409).json({

                    success:
                        false,

                    error:
                        'Este email já possui uma identidade VG90.'

                });

            }


            /*
             * Argon2id é utilizado para armazenar
             * novas palavras-passe.
             */

            const passwordHash =
                await argon2.hash(
                    password,
                    {
                        type:
                            argon2.argon2id
                    }
                );


            const utilizador =
                new User({

                    nome:
                        nome.trim(),

                    telefone:
                        telefone.trim(),

                    email:
                        emailNormalizado,

                    password_hash:
                        passwordHash

                });


            await utilizador.save();


            console.log(
                `👤 Nova identidade criada: ${utilizador.uid}`
            );


            return res.status(201).json({

                success:
                    true,

                message:
                    'Identidade VG90 criada com sucesso.',

                identity:
                    identidadePublica(
                        utilizador
                    )

            });

        }

        catch (error) {

            if (
                error &&
                error.code === 11000
            ) {

                return res.status(409).json({

                    success:
                        false,

                    error:
                        'Email ou UID já existente.'

                });

            }


            console.error(
                '🛑 Erro no registo:',
                error
            );


            return res.status(500).json({

                success:
                    false,

                error:
                    'Não foi possível criar a identidade VG90.'

            });

        }

    }
);


// ==========================================================================
// 15. LOGIN — PORTA ÚNICA DO ECOSSISTEMA
// ==========================================================================

app.post(
    '/api/auth/login',
    async (req, res) => {

        try {

            const {

                email,

                password

            } = req.body || {};


            if (
                typeof email !== 'string' ||
                typeof password !== 'string' ||
                !email.trim() ||
                !password
            ) {

                return res.status(400).json({

                    success:
                        false,

                    error:
                        'Email e senha são obrigatórios.'

                });

            }


            const emailNormalizado =
                email
                    .trim()
                    .toLowerCase();


            const utilizador =
                await User.findOne({

                    email:
                        emailNormalizado

                });


            if (!utilizador) {

                return res.status(401).json({

                    success:
                        false,

                    error:
                        'Credenciais inválidas.'

                });

            }


            const storedHash =
                utilizador.password_hash || '';


            let passwordValida =
                false;


            /*
             * Contas novas:
             * Argon2id.
             */

            if (
                storedHash.startsWith(
                    '$argon2'
                )
            ) {

                passwordValida =
                    await argon2.verify(
                        storedHash,
                        password
                    );

            }


            /*
             * Compatibilidade com contas antigas
             * que ainda usam SHA-256.
             *
             * Depois de um login válido,
             * o hash é automaticamente migrado
             * para Argon2id.
             */

            else {

                const hashAntigo =
                    hashSha256(
                        password
                    );


                const recebido =
                    Buffer.from(
                        storedHash,
                        'utf8'
                    );


                const esperado =
                    Buffer.from(
                        hashAntigo,
                        'utf8'
                    );


                if (
                    recebido.length ===
                    esperado.length
                ) {

                    passwordValida =
                        crypto.timingSafeEqual(
                            recebido,
                            esperado
                        );

                }


                if (passwordValida) {

                    utilizador.password_hash =
                        await argon2.hash(
                            password,
                            {
                                type:
                                    argon2.argon2id
                            }
                        );

                }

            }


            if (!passwordValida) {

                return res.status(401).json({

                    success:
                        false,

                    error:
                        'Credenciais inválidas.'

                });

            }


            /*
             * Regenera o ID da sessão depois
             * de autenticar.
             *
             * Isto reduz risco de session fixation.
             */

            req.session.regenerate(
                async (sessionError) => {

                    if (sessionError) {

                        console.error(
                            '🛑 Erro ao regenerar sessão:',
                            sessionError
                        );


                        return res.status(500).json({

                            success:
                                false,

                            error:
                                'Não foi possível iniciar a sessão.'

                        });

                    }

                    try {

                        utilizador.ultimo_login =
                            new Date();


                        await utilizador.save();


                        req.session.userId =
                            String(
                                utilizador._id
                            );


                        req.session.uid =
                            utilizador.uid;


                        req.session.save(
                            (saveError) => {

                                if (saveError) {

                                    console.error(
                                        '🛑 Erro ao guardar sessão:',
                                        saveError
                                    );


                                    return res.status(500).json({

                                        success:
                                            false,

                                        error:
                                            'Não foi possível guardar a sessão.'

                                    });

                                }


                                console.log(
                                    `🔐 Login autorizado: ${utilizador.uid}`
                                );


                                return res.status(200).json({

                                    success:
                                        true,

                                    message:
                                        'Entrada autorizada no ecossistema VG90.',

                                    identity:
                                        identidadePublica(
                                            utilizador
                                        )

                                });

                            }
                        );

                    }

                    catch (error) {

                        console.error(
                            '🛑 Erro ao atualizar utilizador:',
                            error
                        );


                        return res.status(500).json({

                            success:
                                false,

                            error:
                                'Falha no sistema de autenticação.'

                        });

                    }

                }
            );

        }

        catch (error) {

            console.error(
                '🛑 Erro no login:',
                error
            );


            return res.status(500).json({

                success:
                    false,

                error:
                    'Falha no sistema de autenticação.'

            });

        }

    }
);


// ==========================================================================
// 16. VERIFICAR SESSÃO ATUAL
// ==========================================================================

app.get(
    '/api/auth/me',
    exigirLogin,
    async (req, res) => {

        try {

            const utilizador =
                await User.findById(
                    req.session.userId
                );


            if (!utilizador) {

                return req.session.destroy(
                    () => {

                        return res.status(401).json({

                            success:
                                false,

                            error:
                                'Sessão inválida.'

                        });

                    }
                );

            }


            return res.json({

                success:
                    true,

                identity:
                    identidadePublica(
                        utilizador
                    )

            });

        }

        catch (error) {

            console.error(
                '🛑 Erro ao consultar sessão:',
                error
            );


            return res.status(500).json({

                success:
                    false,

                error:
                    'Erro ao consultar sessão.'

            });

        }

    }
);


// ==========================================================================
// 17. LOGOUT
// ==========================================================================

app.post(
    '/api/auth/logout',
    exigirLogin,
    (req, res) => {

        req.session.destroy(
            (error) => {

                if (error) {

                    return res.status(500).json({

                        success:
                            false,

                        error:
                            'Não foi possível terminar a sessão.'

                    });

                }


                res.clearCookie(
                    'vg90.sid',
                    {

                        httpOnly:
                            true,

                        secure:
                            process.env.NODE_ENV ===
                            'production',

                        sameSite:
                            process.env.COOKIE_SAME_SITE ||
                            'none'

                    }
                );


                return res.json({

                    success:
                        true,

                    message:
                        'Sessão terminada.'

                });

            }
        );

    }
);


// ==========================================================================
// 18. CONSULTAR IDENTIDADE PELO UID
// ==========================================================================

app.get(
    '/api/identity/:uid',
    verificarServicoVG90,
    async (req, res) => {

        try {

            const utilizador =
                await User.findOne({

                    uid:
                        req.params.uid

                }).lean();


            if (!utilizador) {

                return res.status(404).json({

                    success:
                        false,

                    error:
                        'Identidade não encontrada.'

                });

            }


            // Nunca devolver password_hash.

            delete utilizador.password_hash;


            return res.json({

                success:
                    true,

                identity:
                    utilizador

            });

        }

        catch (error) {

            console.error(
                '🛑 Erro ao consultar identidade:',
                error
            );


            return res.status(500).json({

                success:
                    false,

                error:
                    'Erro ao consultar identidade.'

            });

        }

    }
);


// ==========================================================================
// 19. MOTOR MULTIMODAL
// ==========================================================================

async function gerarTextoCopy(
    promptBase
) {

    return new Promise(
        (resolve) => {

            setTimeout(
                () => {

                    resolve({

                        titulo:
                            `🔥 EXPANSÃO RADICAL: ${promptBase}`,

                        copy:
                            `O sistema Vagalume90 gerou uma estratégia para: ${promptBase}.`,

                        hashtags:
                            '#vagalume90 #api #inteligencia'

                    });

                },
                1200
            );

        }
    );

}


async function gerarImagemBanner(
    promptBase
) {

    return new Promise(
        (resolve) => {

            setTimeout(
                () => {

                    resolve({

                        media_url:
                            'https://cdn.vagalume90.com/generated/render_banner_01.png',

                        estilo:
                            'Cyberpunk HUD Interface'

                    });

                },
                1500
            );

        }
    );

}


app.post(
    '/api/ia/completo',
    exigirLogin,
    async (req, res) => {

        try {

            const prompt =
                req.body &&
                req.body.prompt;


            if (
                typeof prompt !== 'string' ||
                !prompt.trim()
            ) {

                return res.status(400).json({

                    success:
                        false,

                    error:
                        'Injeta um prompt válido.'

                });

            }


            const identity =
                await User.findById(
                    req.session.userId
                )
                .select(
                    'uid nome'
                );


            if (!identity) {

                return res.status(401).json({

                    success:
                        false,

                    error:
                        'Sessão inválida.'

                });

            }


            const [
                copyGerada,
                imagemGerada
            ] =
                await Promise.all([

                    gerarTextoCopy(
                        prompt.trim()
                    ),

                    gerarImagemBanner(
                        prompt.trim()
                    )

                ]);


            return res.status(200).json({

                success:
                    true,

                status_sistema:
                    'CORE_CONNECTED',

                identity: {

                    uid:
                        identity.uid,

                    nome:
                        identity.nome

                },

                payload: {

                    texto:
                        copyGerada,

                    imagem:
                        imagemGerada

                }

            });

        }

        catch (error) {

            console.error(
                'Erro no motor IA:',
                error
            );


            return res.status(500).json({

                success:
                    false,

                error:
                    'Falha crítica nos nós de IA.'

            });

        }

    }
);


// ==========================================================================
// 20. ZONA DE GUERRA / ARENA
// ==========================================================================

const desafiosArena = {

    opt_01: {

        id:
            'opt_01',

        resposta_chave:
            'low-data-metric',

        xp_recompensa:
            400

    }

};


app.post(
    '/api/guerra/submeter',
    exigirLogin,
    async (req, res) => {

        try {

            const {

                desafio_id,

                resposta_utilizador

            } =
                req.body || {};


            const guerreiro =
                await User.findById(
                    req.session.userId
                );


            if (!guerreiro) {

                return res.status(401).json({

                    success:
                        false,

                    error:
                        'Sessão inválida.'

                });

            }


            const desafio =
                desafiosArena[
                    desafio_id
                ];


            if (!desafio) {

                return res.status(400).json({

                    success:
                        false,

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
                        guerreiro.combate.precisao_prompts -
                            10
                    );


                await guerreiro.save();


                return res.status(200).json({

                    success:
                        true,

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


            guerreiro.combate.desafios_concluidos +=
                1;


            await guerreiro.save();


            if (
                guerreiro.combate.xp >=
                2000
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
                        upsert:
                            true,

                        new:
                            true
                    }

                );

            }


            return res.status(200).json({

                success:
                    true,

                status_combate:
                    'VITÓRIA',

                novo_xp:
                    guerreiro.combate.xp,

                status_sistema:
                    guerreiro.status_sistema

            });

        }

        catch (error) {

            console.error(
                'Erro na Arena:',
                error
            );


            return res.status(500).json({

                success:
                    false,

                error:
                    'Erro no processamento da Arena.'

            });

        }

    }
);


// ==========================================================================
// 21. MERCADO — REGISTAR AQUISIÇÃO
// ==========================================================================

app.post(
    '/api/mercado/comprar',
    exigirLogin,
    async (req, res) => {

        try {

            const {

                produto_id,

                afiliado_cod

            } =
                req.body || {};


            if (
                typeof produto_id !== 'string' ||
                !produto_id.trim()
            ) {

                return res.status(400).json({

                    success:
                        false,

                    error:
                        'produto_id é obrigatório.'

                });

            }


            const comprador =
                await User.findById(
                    req.session.userId
                )
                .select(
                    'uid'
                );


            if (!comprador) {

                return res.status(401).json({

                    success:
                        false,

                    error:
                        'Sessão inválida.'

                });

            }


            const transacao_id =
                `TX_${crypto.randomUUID()}`;


            const novaTransacao =
                new Transacao({

                    transacao_id,

                    produto_id:
                        produto_id.trim(),

                    produto_titulo:
                        'Produto Digital',

                    comprador_id:
                        comprador.uid,

                    afiliado_cod:
                        typeof afiliado_cod ===
                        'string'
                            ? afiliado_cod
                            : '',

                    status:
                        'AGUARDANDO PROVA'

                });


            await novaTransacao.save();


            if (N8N_WEBHOOK_URL) {

                try {

                    const response =
                        await fetch(
                            N8N_WEBHOOK_URL,
                            {

                                method:
                                    'POST',

                                headers: {

                                    'Content-Type':
                                        'application/json'

                                },

                                body:
                                    JSON.stringify({

                                        event:
                                            'requisicao_aquisicao',

                                        transacao_id,

                                        produto_id:
                                            novaTransacao.produto_id,

                                        comprador_id:
                                            comprador.uid,

                                        afiliado_cod:
                                            novaTransacao.afiliado_cod,

                                        status:
                                            novaTransacao.status

                                    }),

                                signal:
                                    AbortSignal.timeout(
                                        8000
                                    )

                            }
                        );


                    if (!response.ok) {

                        console.warn(
                            `⚠️ n8n respondeu com HTTP ${response.status}`
                        );

                    }

                }

                catch (error) {

                    console.warn(
                        '⚠️ n8n não respondeu; transação ficou guardada no MongoDB.'
                    );

                }

            }


            return res.status(201).json({

                success:
                    true,

                transacao_id,

                status:
                    novaTransacao.status

            });

        }

        catch (error) {

            console.error(
                'Erro no Mercado:',
                error
            );


            return res.status(500).json({

                success:
                    false,

                error:
                    'Erro ao processar aquisição.'

            });

        }

    }
);


// ==========================================================================
// 22. INFORMAÇÃO PÚBLICA DA IDENTIDADE
// ==========================================================================

app.get(
    '/api/identity/:uid/public',
    async (req, res) => {

        try {

            const utilizador =
                await User.findOne({

                    uid:
                        req.params.uid

                })
                .select(
                    'uid nome afiliado_id status_sistema combate.nivel combate.xp'
                )
                .lean();


            if (!utilizador) {

                return res.status(404).json({

                    success:
                        false,

                    error:
                        'Identidade não encontrada.'

                });

            }


            return res.json({

                success:
                    true,

                identity:
                    utilizador

            });

        }

        catch (error) {

            return res.status(500).json({

                success:
                    false,

                error:
                    'Erro ao consultar identidade.'

            });

        }

    }
);


// ==========================================================================
// 23. ERROS
// ==========================================================================

app.use(
    (err, req, res, next) => {

        if (
            err &&
            err.message ===
                'Origem não autorizada pelo CORS.'
        ) {

            return res.status(403).json({

                success:
                    false,

                error:
                    'Origem não autorizada.'

            });

        }


        if (
            err instanceof SyntaxError &&
            err.status === 400 &&
            'body' in err
        ) {

            return res.status(400).json({

                success:
                    false,

                error:
                    'JSON inválido.'

            });

        }


        console.error(
            '🛑 Erro não tratado:',
            err
        );


        return res.status(500).json({

            success:
                false,

            error:
                'Erro interno do servidor.'

        });

    }
);


// ==========================================================================
// 24. CONEXÃO MONGODB + ARRANQUE
// ==========================================================================

mongoose
    .connect(
        MONGO_URI
    )

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


