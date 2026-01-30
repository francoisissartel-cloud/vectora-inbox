# 💬 Comment Prompter Amazon Q Developer

**Guide complet**: `docs/GUIDE_PROMPTER_Q_DEVELOPER.md`

---

## 🎯 Principe

**Q lit automatiquement `.q-context/vectora-inbox-development-rules.md`**

Vous n'avez PAS besoin de rappeler les règles !

---

## 📝 Formule Simple

```
[ACTION] + [OBJECTIF] + [Environnement optionnel]
```

---

## ✅ Exemples de Bons Prompts

### Développement
```
Ajoute une fonction pour extraire les dates relatives.

Environnement: dev
```

### Correction Bug
```
Le matching Bedrock échoue avec les caractères spéciaux.
Corrige ça.
```

### Configuration
```
Ajoute 3 nouvelles entités dans tech_lai_ecosystem.

Sync vers dev.
```

### Promotion
```
La version 1.2.4 fonctionne bien en dev.
Promeus en stage.
```

### Tests
```
Teste normalize-score-v2 avec lai_weekly_v7.
```

---

## 🤖 Ce que Q Fait Automatiquement

✅ Lit les règles de gouvernance  
✅ Applique le workflow (Build → Deploy → Test)  
✅ Incrémente VERSION  
✅ Utilise les scripts standardisés  
✅ Teste en dev avant stage  
✅ Commit proprement  

---

## 🌍 Environnements

**Par défaut**: dev

**Préciser si besoin**:
- `Environnement: dev` - Développement
- `Environnement: stage` - Pré-production
- `Workflow: dev → stage` - Complet

---

## ❌ À Éviter

❌ Trop de détails techniques  
❌ Rappeler les règles  
❌ Commandes AWS directes  

**Q sait déjà comment faire !**

---

## 💡 Astuce

**Laissez Q proposer des solutions**:

```
Je veux améliorer la performance du matching Bedrock.
```

Q va proposer plusieurs approches et vous demander laquelle vous préférez.

---

**Vous décrivez ce que vous voulez, Q fait le reste !**
