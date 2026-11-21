// The backend chapter is English; every other chapter is Arabic.
const english = /(?:^|\/)backend(?:\.|\/|$)/.test(window.location.pathname);
document.documentElement.lang = english ? 'en' : 'ar';
document.documentElement.dir = english ? 'ltr' : 'rtl';
