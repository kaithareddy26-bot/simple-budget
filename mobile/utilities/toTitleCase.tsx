export default function toTitleCase(str: string) {
    //Split the string into seperate words
    const words = str.split(" ");
    //Each first letter should be capitalized.
    for (let i = 0; i < words.length; i++){
        words[i] = words[i].charAt(0).toUpperCase() + words[i].slice(1).toLowerCase();
    }
    return words.join(" ");
}