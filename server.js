/**
 * VAGALUME90 CORE ENGINE — TUDO-EM-UM
 * MongoDB base: teste
 * Coleção de identidades: Usuários
 *
 * Renderização de variáveis:
 * MONGO_URI, SESSION_SECRET, VG90_SERVICE_SECRET (opcional),
 * CORS_ORIGIN (opcional), COOKIE_SAME_SITE (opcional),
 * N8N_WEBHOOK_URL (opcional), NODE_ENV, PORT
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

const PORT = process.env.PORT || 3000;
const MONGO_URI = process.env.MONGO_URI;
const SESSION_SECRET = process.env.SESSION_SECRET || '';
const VG90_SERVICE_SECRET = process.env.VG90_SERVICE_SECRET || '';
const N8N_WEBHOOK_URL = process.env.N8N_WEBHOOK_URL || '';
const DB_NAME = 'teste';
const USER_COLLECTION = 'Usuários';

if (!MONGO_URI) {
  console.error('MONGO_URI não configurado no Render.');
  process.exit(1);
}

se (SESSION_SECRET.length < 32) {
  console.error('SESSION_SECRET deve ter pelo menos 32 caracteres.');
  process.exit(1);
}

// CORS
const allowedOrigins = (process.env.CORS_ORIGIN || '')
  .dividir(',')
  .map(valor => valor.trim())
  .filter(Boolean);

app.use(cors({
  origem(origem, retorno de chamada) {
    se (!origem || origensPermitidas.comprimento === 0 || origensPermitidas.inclui(origem)) {
      retornar callback(null, true);
    }
    return callback(new Error('Origem não autorizada pelo CORS.'));
  },
  credenciais: verdadeiro,
  métodos: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  cabeçalhos permitidos: ['Content-Type', 'X-VG90-Service-Key']
}));

app.use(express.json({ limit: '1mb' }));
app.set('trust proxy', 1);

// Cookies cross-site desabilitam SameSite=None e Secure=true.
// Em produção no Render, Secure fica ativo.
const isProduction = process.env.NODE_ENV === 'production';
const sameSiteSetting = (process.env.COOKIE_SAME_SITE || 'none').toLowerCase();
const cookieSameSite = ['lax', 'strict', 'none'].includes(sameSiteSetting)
  ? sameSiteSetting
  : 'nenhum';
const cookieSecure = isProduction || cookieSameSite === 'none';

app.use(session({
  nome: 'vg90.sid',
  segredo: SESSION_SECRET,
  salvar novamente: falso,
  salvarNãoInicializado: falso,
  rolando: verdadeiro,
  loja: MongoStore.create({
    mongoUrl: MONGO_URI,
    Nome do banco de dados: DB_NAME,
    Nome da coleção: 'vg90_sessions',
    ttl: 7 * 24 * 60 * 60
  }),
  cookie: {
    httpOnly: verdadeiro,
    seguro: cookieSecure,
    mesmoSite: cookieSameSite,
    idadeMáxima: 7 * 24 * 60 * 60 * 1000
  }
}));

// Middleware: autenticação entre serviços VG90.
função verificarServicoVG90(req, res, next) {
  se (!VG90_SERVICE_SECRET) {
    retornar res.status(503).json({
      sucesso: falso,
      erro: 'Autenticação interna não configurada.'
    });
  }

  const recebido = Buffer.from(req.get('X-VG90-Service-Key') || '', 'utf8');
  const esperado = Buffer.from(VG90_SERVICE_SECRET, 'utf8');

  if (recebida.length !== esperados.length ||
      !crypto.timingSafeEqual(recebida, expectativas)) {
    retornar res.status(401).json({
      sucesso: falso,
      erro: 'Serviço não autorizado.'
    });
  }
  retornar próximo();
}

função exigirLogin(req, res, next) {
  se (!req.session || !req.session.userId) {
    retornar res.status(401).json({
      sucesso: falso,
      erro: 'Iniciar sessão para continuar.'
    });
  }
  retornar próximo();
}

função hashSha256(senha) {
  retornar crypto.createHash('sha256').update(password).digest('hex');
}

função gerarUID() {
  retornar `VGLM-${crypto.randomInt(1000, 10000)}`;
}

function identidadePublica(utilizador) {
  retornar {
    uid: usuário.uid,
    Nome: usuário .nome,
    telefone: usuário.telefone,
    email: seguir.email,
    afiliado_id: usuário.afiliado_id,
    carteira_kwanzas: usuário.carteira_kwanzas,
    combate: usuário.combate,
    status_sistema: usuário.status_sistema,
    ultima_login: usuário.ultimo_login
  };
}

// IDENTIDADE VG90
const UserSchema = novo mongoose.Schema({
  uid: {
    tipo: String,
    Obrigatório: verdadeiro,
    único: verdadeiro,
    índice: verdadeiro,
    padrão: gerarUID
  },
  nome: { type: String, required: true, trim: true },
  telefone: { type: String, required: true, trim: true },
  e-mail: {
    tipo: String,
    Obrigatório: verdadeiro,
    único: verdadeiro,
    índice: verdadeiro,
    minúsculas: verdadeiro,
    aparar: verdadeiro
  },
  hash_da_senha: { tipo: String, obrigatório: true, selecionar: false },
  afiliado_id: { type: String, unique: true, sparse: true },
  carteira_kwanzas: { tipo: Número, padrão: 0 },
  combate: {
    nível: { tipo: Número, padrão: 1 },
    xp: { tipo: Número, padrão: 0 },
    desafios_concluidos: { tipo: Número, padrão: 0 },
    precisao_prompts: { type: Number, default: 100 }
  },
  status_sistema: {
    tipo: String,
    padrão: 'ACRESCENTANDO_ENERGIA',
    enum: ['ACRESCENTANDO_ENERGIA', 'FOCADO', 'ELITE_MUTANTE']
  },
  criado_em: { tipo: Data, padrão: Date.now },
  ultimo_login: { tipo: Data, padrão: nulo }
});

// O terceiro argumento fixa o nome exato da coleção no Atlas.
UserSchema.pre('save', function(next) {
  se (!this.afiliado_id) {
    this.afiliado_id = `partner_${this.uid.toLowerCase()}_matrix`;
  }

  if (this.combate.xp >= 2000 && this.carteira_kwanzas > 50000) {
    this.status_sistema = 'ELITE_MUTANTE';
  } senão se (this.combate.xp > 1000) {
    this.status_sistema = 'FOCADO';
  } outro {
    this.status_sistema = 'ACRESCENTANDO_ENERGIA';
  }
  próximo();
});

const User = mongoose.model('User', UserSchema, USER_COLLECTION);

// MERCADO DE TALENTOS
const FreelancerSchema = new mongoose.Schema({
  ID do usuário: {
    tipo: mongoose.Schema.Types.ObjectId,
    ref: 'Usuário',
    Obrigatório: verdadeiro,
    único: verdadeiro
  },
  especialidade: { tipo: String, padrão: 'Programação' },
  badge_guerra_verificado: { tipo: Booleano, padrão: falso },
  criado_em: { tipo: Data, padrão: Date.now }
});
const Freelancer = mongoose.model('Freelancer', FreelancerSchema);

// TRANSAÇÕES
const TransacaoSchema = new mongoose.Schema({
  transacao_id: { type: String, unique: true, required: true },
  produto_id: { type: String, required: true },
  produto_titulo: { type: String, required: true },
  comprador_id: { type: String, required: true },
  afiliado_cod: { type: String, default: '' },
  status: { type: String, default: 'AGUARDANDO PROVA' },
  timestamp: { type: Date, default: Date.now }
});
const Transacao = mongoose.model('Transacao', TransacaoSchema);

// SAÚDE
app.get('/health', (req, res) => {
  const connected = mongoose.connection.readyState === 1;
  res.status(conectado ? 200 : 503).json({
    status: conectado ? 'ok' : 'degradado',
    Projeto: 'Vagalume90 Core',
    versão: '3.4.0',
    núcleo: conectado ? 'online' : 'iniciando',
    banco de dados: conectado ? 'conectado' : 'desconectado',
    nome_do_banco_de_dados: DB_NAME,
    identidade: 'ativado',
    coleção_de_usuários: COLEÇÃO_DE_USUÁRIOS,
    módulos: { identidade: verdadeiro, IA: verdadeiro, arena: verdadeiro, mercado: verdadeiro }
  });
});

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'templates', 'index.html'), err => {
    se (erro && !res.headersSent) {
      res.status(200).send('VAGALUME90 CORE ONLINE. Usa /health para verificar o estado.');
    }
  });
});

app.get('/api/status', (req, res) => {
  res.json({
    Sistema: 'VAGALUME90 CORE',
    status: mongoose.connection.readyState === 1 ? 'ONLINE' : 'INICIANDO',
    versão: '3.4.0',
    identidade: verdadeira,
    banco de dados: mongoose.connection.readyState === 1 ? 'CONECTADO' : 'DESCONECTADO',
    nome_do_banco_de_dados: DB_NAME,
    coleção_de_usuários: COLEÇÃO_DE_USUÁRIOS,
    mensagem: 'Estado do Core central VG90.'
  });
});

app.get('/painel', requerLogin, (req, res) => {
  res.sendFile(path.join(__dirname, 'templates', 'painel.html'));
});

// REGISTRO
app.post('/api/auth/register', async (req, res) => {
  tentar {
    const { nome, telefone, email, senha } = req.body || {};

    se ([nome, telefone, email, senha].algum(valor => tipo de valor !== 'string') ||
        !nome.trim() || !telefone.trim() || !email.trim() || !senha) {
      retornar res.status(400).json({
        sucesso: falso,
        erro: 'Nome, telefone, email e senha são obrigatórios.'
      });
    }

    se (senha.comprimento < 8) {
      retornar res.status(400).json({
        sucesso: falso,
        erro: 'A senha deve ter pelo menos 8 caracteres.'
      });
    }

    const emailNormalizado = email.trim().toLowerCase();
    const existente = await User.findOne({ email: emailNormalizado }).select('+password_hash');

    se (existente) {
      retornar res.status(409).json({
        sucesso: falso,
        erro: 'Este email já possui uma identidade VG90.'
      });
    }

    const passwordHash = await argon2.hash(password, { type: argon2.argon2id });
    const Caixa = novo Usuário({
      nome: nome.trim(),
      telefone: telefone.trim(),
      email: emailNormalizado,
      hash_da_senha: hash_da_senha
    });

    aguarde o usuário.save();

    console.log(`Nova identidade VG90 criada: ${utilizador.uid}`);
    retornar res.status(201).json({
      sucesso: verdadeiro,
      mensagem: 'Identidade VG90 criada com sucesso.',
      identidade: identidadePublica(utilizador)
    });
  } catch (erro) {
    se (erro && código de erro === 11000) {
      retornar res.status(409).json({
        sucesso: falso,
        erro: 'E-mail, UID ou código de afiliado já existente.'
      });
    }
    console.error('Erro no registro:', erro);
    retornar res.status(500).json({
      sucesso: falso,
      erro: 'Não foi possível criar a identidade VG90.'
    });
  }
});

// CONECTE-SE
app.post('/api/auth/login', async (req, res) => {
  tentar {
    const { email, password } = req.body || {};

    se (tipo de email !== 'string' || tipo de senha !== 'string' ||
        !email.trim() || !senha) {
      retornar res.status(400).json({
        sucesso: falso,
        erro: 'E-mail e senha são obrigatórios.'
      });
    }

    const usuário = aguarda User.findOne({
      email: email.trim().toLowerCase()
    }).select('+password_hash');

    se (!utilizador) {
      retornar res.status(401).json({
        sucesso: falso,
        erro: 'Credenciais inválidos.'
      });
    }

    const armazenadoHash = usuário.password_hash || '';
    let passwordValida = false;

    se (storedHash.startsWith('$argon2')) {
      senhaValida = aguarde argon2.verificar(hash armazenado, senha);
    } outro {
      const recebido = Buffer.from(storedHash, 'utf8');
      const esperado = Buffer.from(hashSha256(senha), 'utf8');
      if (recebido.length === esperado.length) {
        passwordValida = crypto.timingSafeEqual(recebido, esperado);
      }
      se (senhaVálida) {
        usuário.password_hash = await argon2.hash(password, {
          tipo: argon2.argon2id
        });
      }
    }

    se (!senhaVálida) {
      retornar res.status(401).json({
        sucesso: falso,
        erro: 'Credenciais inválidos.'
      });
    }

    req.session.regenerate(async sessionError => {
      se (erro de sessão) {
        console.error('Erro ao regenerar sessão:', sessionError);
        retornar res.status(500).json({
          sucesso: falso,
          erro: 'Não foi possível iniciar a sessão.'
        });
      }

      tentar {
        usuário.ultimo_login = new Data();
        aguarde o usuário.save();

        req.session.userId = String(utilizador._id);
        req.session.uid = usuário.uid;

        req.session.save(saveError => {
          se (saveError) {
            console.error('Erro ao salvar sessão:', saveError);
            retornar res.status(500).json({
              sucesso: falso,
              erro: 'Não foi possível salvar a sessão.'
            });
          }

          retornar res.status(200).json({
            sucesso: verdadeiro,
            mensagem: 'Entrada autorizada no ecossistema VG90.',
            identidade: identidadePublica(utilizador)
          });
        });
      } catch (erro) {
        console.error('Erro ao atualizar usuário:', erro);
        retornar res.status(500).json({
          sucesso: falso,
          erro: 'Falha no sistema de autenticação.'
        });
      }
    });
  } catch (erro) {
    console.error('Erro sem login:', erro);
    retornar res.status(500).json({
      sucesso: falso,
      erro: 'Falha no sistema de autenticação.'
    });
  }
});

// SESSÃO ATUAL
app.get('/api/auth/me', exigirLogin, async (req, res) => {
  tentar {
    const usuário = await User.findById(req.session.userId);
    se (!utilizador) {
      retornar req.session.destroy(() => res.status(401).json({
        sucesso: falso,
        erro: 'Sessão inválida.'
      }));
    }
    retornar res.json({
      sucesso: verdadeiro,
      identidade: identidadePublica(utilizador)
    });
  } catch (erro) {
    console.error('Erro ao consultar sessão:', erro);
    retornar res.status(500).json({
      sucesso: falso,
      error: 'Erro ao consultar sessão.'
    });
  }
});

// SAIR
app.post('/api/auth/logout', exigirLogin, (req, res) => {
  req.session.destroy(error => {
    se (erro) {
      retornar res.status(500).json({
        sucesso: falso,
        erro: 'Não foi possível terminar a sessão.'
      });
    }
    res.clearCookie('vg90.sid', {
      httpOnly: verdadeiro,
      seguro: cookieSecure,
      mesmoSite: cookieSameSite
    });
    return res.json({ sucesso: verdadeiro, mensagem: 'Sessão encerrada.' });
  });
});

// CONSULTA INTERNA DE IDENTIDADE
app.get('/api/identity/:uid', verificarServicoVG90, async (req, res) => {
  tentar {
    const usuário = await User.findOne({ uid: req.params.uid }).lean();
    se (!utilizador) {
      retornar res.status(404).json({
        sucesso: falso,
        erro: 'Identidade não encontrada.'
      });
    }
    excluir usuário.password_hash;
    return res.json({sucesso: verdadeiro, identidade: usuário });
  } catch (erro) {
    console.error('Erro ao consultar identidade:', erro);
    retornar res.status(500).json({
      sucesso: falso,
      error: 'Erro ao consultar identidade.'
    });
  }
});

// IA — resposta demonstrativa local, não é geração real por modelo externo.
função assíncrona gerarTextoCopy(promptBase) {
  retornar {
    título: `Estratégia VG90: ${promptBase}`,
    copy: `Pedido recebido pelo Core VG90: ${promptBase}.`,
    hashtags: '#vagalume90 #vg90 #tecnologia'
  };
}

função assíncrona gerarImagemBanner(promptBase) {
  retornar {
    media_url: nulo,
    estilo: 'Cyberfuture',
    mensagem: 'A geração real de imagem ainda precisa de um fornecedor de IA configurado.',
    prompt: promptBase
  };
}

app.post('/api/ia/completo', exigeLogin, async (req, res) => {
  tentar {
    const prompt = req.body && req.body.prompt;
    if (typeof prompt !== 'string' || !prompt.trim()) {
      retornar res.status(400).json({
        sucesso: falso,
        erro: 'Envia um prompt válido.'
      });
    }

    const identity = await User.findById(req.session.userId).select('uid nome');
    se (!identidade) {
      retornar res.status(401).json({
        sucesso: falso,
        erro: 'Sessão inválida.'
      });
    }

    const [copyGerada, imagemGerada] = aguarda Promise.all([
      gerarTextoCopy(prompt.trim()),
      gerarImagemBanner(prompt.trim())
    ]);

    retornar res.json({
      sucesso: verdadeiro,
      status_sistema: 'CORE_CONNECTED',
      identidade: { uid: identidade.uid, nome: identidade.nome },
      carga útil: { texto: copyGerada, imagem: imagemGerada }
    });
  } catch (erro) {
    console.error('Erro no motor IA:', erro);
    retornar res.status(500).json({
      sucesso: falso,
      erro: 'Falha no motor de IA.'
    });
  }
});

// ARENA
const desafiosArena = {
  opt_01: {
    id: 'opt_01',
    resposta_chave: 'métrica de dados baixos',
    xp_recompensa: 400
  }
};

app.post('/api/guerra/submeter', exigeLogin, async (req, res) => {
  tentar {
    const { desafio_id, resposta_utilizador } = req.body || {};
    const guerreiro = await User.findById(req.session.userId);

    se (!guerreiro) {
      retornar res.status(401).json({
        sucesso: falso,
        erro: 'Sessão inválida.'
      });
    }

    const desafio = desafiosArena[desafio_id];
    se (!desafio) {
      retornar res.status(400).json({
        sucesso: falso,
        erro: 'Desafio norma.'
      });
    }

    const resposta = String(resposta_utilizador || '').toLowerCase();
    const isCorreto = resposta.includes(desafio.resposta_chave);

    se (!isCorreto) {
      guerreiro.combate.precisao_prompts = Math.max(
        0,
        guerreiro.combate.precisao_prompts - 10
      );
      aguarde guerreiro.save();
      retornar res.json({
        sucesso: verdadeiro,
        status_combate: 'DERROTA',
        precisão: guerreiro.combate.precisao_prompts,
        novo_xp: guerreiro.combate.xp,
        status_sistema: guerreiro.status_sistema
      });
    }

    guerreiro.combate.xp += desafio.xp_recompensa;
    guerreiro.combate.desafios_concluidos += 1;
    aguarde guerreiro.save();

    if (guerreiro.combate.xp >= 2000) {
      aguarde Freelancer.findOneAndUpdate(
        { user_id: guerreiro._id },
        { $set: { badge_guerra_verificado: true } },
        { upsert: true, new: true, setDefaultsOnInsert: true }
      );
    }

    retornar res.json({
      sucesso: verdadeiro,
      status_combate: 'VITÓRIA',
      novo_xp: guerreiro.combate.xp,
      status_sistema: guerreiro.status_sistema
    });
  } catch (erro) {
    console.error('Erro na Arena:', erro);
    retornar res.status(500).json({
      sucesso: falso,
      erro: 'Erro no processamento da Arena.'
    });
  }
});

// MERCADO — REGISTAR AQUISIÇÃO
app.post('/api/mercado/comprar', exigênciaLogin, async (req, res) => {
  tentar {
    const produto {id_id, afiliado_cod } = req.body || {};
    if (typeof produto_id !== 'string' || !produto_id.trim()) {
      retornar res.status(400).json({
        sucesso: falso,
        erro: 'produto_id é obrigatório.'
      });
    }

    const comprador = await User.findById(req.session.userId).select('uid');
    se (!comprador) {
      retornar res.status(401).json({
        sucesso: falso,
        erro: 'Sessão inválida.'
      });
    }

    const transacao_id = `TX_${crypto.randomUUID()}`;
    const novaTransação = new Transação({
      id_da_transação,
      produto_id: produto_id.trim(),
      produto_titulo: 'Produto Digital',
      id_do_comprador: comprador.uid,
      afiliado_cod: typeof afiliado_cod === 'string' ? afiliado_cod.trim() : '',
      status: 'AGUARDANDO PROVA'
    });

    aguarde novaTransação.save();

    se (N8N_WEBHOOK_URL) {
      tentar {
        const response = await fetch(N8N_WEBHOOK_URL, {
          método: 'POST',
          cabeçalhos: { 'Content-Type': 'application/json' },
          corpo: JSON.stringify({
            evento: 'requisicao_aquisicao',
            id_da_transação,
            produto_id: novaTransacao.produto_id,
            id_do_comprador: comprador.uid,
            afiliado_cod: novaTransacao.afiliado_cod,
            status: novaTransacao.status
          }),
          sinal: AbortSignal.timeout(8000)
        });

        se (!response.ok) {
          console.warn(`n8n respondeu com HTTP ${response.status}`);
        }
      } catch (erro) {
        console.warn('n8n indisponível; a transação ficou guardada no MongoDB.');
      }
    }

    retornar res.status(201).json({
      sucesso: verdadeiro,
      id_da_transação,
      status: novaTransacao.status
    });
  } catch (erro) {
    console.error('Erro no Mercado:', erro);
    retornar res.status(500).json({
      sucesso: falso,
      error: 'Erro ao processar aquisição.'
    });
  }
});

// IDENTIDADE PÚBLICA LIMITADA
app.get('/api/identity/:uid/public', async (req, res) => {
  tentar {
    const usuário = await User.findOne({ uid: req.params.uid })
      .select('uid nome afiliado_id status_sistema combate.nivel combate.xp')
      .magro();

    se (!utilizador) {
      retornar res.status(404).json({
        sucesso: falso,
        erro: 'Identidade não encontrada.'
      });
    }
    return res.json({sucesso: verdadeiro, identidade: usuário });
  } catch (erro) {
    console.error('Erro ao consultar identidade pública:', erro);
    retornar res.status(500).json({
      sucesso: falso,
      error: 'Erro ao consultar identidade.'
    });
  }
});

// ERROS
app.use((err, req, res, next) => {
  if (err && err.message === 'Origem não autorizada pelo CORS.') {
    retornar res.status(403).json({
      sucesso: falso,
      erro: 'Origem não autorizada.'
    });
  }

  se (err instanceof SyntaxError && err.status === 400 && 'body' in err) {
    retornar res.status(400).json({
      sucesso: falso,
      erro: 'JSON não.'
    });
  }

  console.error('Erro não tratado:', err);
  retornar res.status(500).json({
    sucesso: falso,
    erro: 'Erro interno do servidor.'
  });
});

// LIGAÇÃO À BASE teste E ARRANQUE
mongoose.connect(MONGO_URI, {
  Nome do banco de dados: DB_NAME,
  serverSelectionTimeoutMS: 15000
})
.then(() => {
  console.log(`MongoDB ligado. Base: ${DB_NAME}`);
  console.log(`Coleção de identidades: ${USER_COLLECTION}`);
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`VAGALUME90 CORE ativo na porta ${PORT}`);
  });
})
.catch(erro => {
  console.error('Falha de conexão MongoDB:', error.message);
  process.exit(1);
});