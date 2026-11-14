import type { RecommendResponse } from "./types";

export const MOCK_RESPONSE: RecommendResponse = {
  source: "mock",
  recommendations: [
    {
      id: "out_cafe_maure", type: "outdoor", category_tag: "SORTIE LOCALE", tag_color: "sauge",
      title: "Thé à la menthe au Café Maure", location_name: "OUDAYAS, RABAT",
      image_url: "",
      description: "Une terrasse paisible au-dessus du Bouregreg, idéale pour discuter loin du bruit.",
      maps_url: "https://www.google.com/maps/search/?api=1&query=Caf%C3%A9+Maure+Oudayas+Rabat",
    },
    {
      id: "act_moodboard", type: "indoor", category_tag: "ATELIER CRÉATIF", tag_color: "peche",
      title: "Moodboard visuel sur papier", location_name: "À LA MAISON",
      image_url: "",
      description: "Prends 20 minutes pour découper et assembler tes idées du moment, sans aucun écran.",
      maps_url: null,
      instructions: [
        "Rassemble magazines, ciseaux, colle et une feuille A3.",
        "Pendant 10 minutes, découpe tout ce qui t'attire sans réfléchir.",
        "Assemble les morceaux en 10 minutes, sans chercher la perfection.",
        "Donne un titre d'un seul mot à ton moodboard.",
      ],
    },
    {
      id: "cap_camus", type: "indoor", category_tag: "CAPSULE INTELLECTUELLE", tag_color: "lilas",
      title: "Camus — Le Mythe de Sisyphe", location_name: "À LA MAISON",
      image_url: "",
      description: "« Il faut imaginer Sisyphe heureux. » Un extrait court suivi d'une question à méditer.",
      maps_url: null,
      instructions: [
        "Lis le dernier chapitre « Le Mythe de Sisyphe » (environ 5 pages).",
        "Souligne une phrase qui te dérange ou te touche.",
        "Question : quel est ton rocher en ce moment ?",
        "Écris 5 lignes, ou débattez-en si vous êtes deux.",
      ],
    },
  ],
};
