let LOADING_INTERVAL = "stopped",
	GETSTATUS_INTERVAL,
	STOPPED = false;
document.getElementById("submit").addEventListener("click", submit);
// GETSTATUS_INTERVAL = setInterval(getstatus, 2000);
getstatus();

function hide_welcome() {
	const element = document.querySelector(".welcome");
	element.classList.add("welcome-hide");
	const login = document.querySelector(".login");
	login.classList.remove("hidden");
}

function hide_login() {
	const element = document.querySelector(".login");
	element.classList.add("hidden");
}

function login_error() {
	const errmsg = document.querySelector("#errmsg");
	errmsg.classList.remove("hidden");
	const login = document.querySelector(".login");
	login.classList.remove("hidden");
}

function loading_start() {
	if (LOADING_INTERVAL !== "stopped") return;
	const element = document.querySelector(".loading");
	element.classList.remove("hidden");
	LOADING_INTERVAL = setInterval(() => {
		const element = document.getElementById("loading-dots");
		if (element.textContent === "...") {
			element.textContent = ".";
		} else {
			element.textContent += ".";
		}
	}, 1000 / 3);
}

function loading_stop() {
	const element = document.querySelector(".loading");
	element.classList.add("hidden");
	clearInterval(LOADING_INTERVAL);
	LOADING_INTERVAL = "stopped";
}

function titleCase(str) {
	let splitStr = str.toLowerCase().split(" ");
	for (let i = 0; i < splitStr.length; i++) {
		splitStr[i] =
			splitStr[i].charAt(0).toUpperCase() + splitStr[i].substring(1);
	}
	return splitStr.join(" ");
}

function loading_change(text) {
	const element = document.getElementById("loading-text");
	if (text.includes("parser:")) {
		text = text.replace("parser:", "");
	}
	if (text.includes("extracting_page:")) {
		text = text.split(":").join(" ");
	}
	if (text.includes("_")) {
		text = text.split("_").join(" ");
	}
	if (document.querySelector('html').getAttribute('lang') === 'ru') {
		text = text.replace('launched', 'система запущена')
					.replace('created', 'драйвер создан')
					.replace('driver initialized', 'драйвер инициализирован')
					.replace('extracting page', 'извлечение страницы')
	}
	text = titleCase(text).trim();
	if (element.textContent === text) return;
	element.classList.remove("loading-text-new");
	setTimeout(() => {
		element.textContent = text;
		element.classList.add("loading-text-new");
	}, 500);
}

async function getstatus() {
	if (STOPPED) return;
	await sendData("/status", "GET").then(async (response) => {
		const status = response.status;
		console.log("Status: ", status);
		loading_change(status);
		if (status === "launched") {
			hide_welcome();
		} else if (status === "parser:created" || status === "parser:driver_initialized" ||
				   status === "parser:login_successful" || status.startsWith("parser:extracting")) {
				hide_welcome();
				hide_login();
			if (LOADING_INTERVAL === "stopped") {
				loading_start();
			}
		} else if (status === "parser:login_error") {
			login_error();
		} else if (status === "parser:extraction_successful") {
			STOPPED = true;
			await sendData("/result", "GET").then((response) => {
				console.log("Result: ", response.data);
				hide_welcome();
				hide_login();
				loading_stop();
				showresults(response.data);
			});
		} else if (status === "parser:error") {
			STOPPED = true;
			if (document.querySelector('html').getAttribute('lang') === 'ru') {
				alert('Обнаружена ошибка. \n Пожалуйста, попробуйте позже. \n \n' +
					'Если проблема не исчезнет, вы можете связаться с разработчиком: ' + 'ut8cskef' + '@' + 'anonaddy.me' + ' \n' +
					'Не забудьте добавить подробности о том, что вы делали до появления ошибки. \n \n' +
					'Теперь вы будете перенаправлены на домашнюю страницу.');
			} else {
				alert('Encountered error. \n Please, try again later. \n \n' +
					'If problem persists you may contact the developer: ' + 'ut8cskef' + '@' + 'anonaddy.me' + ' \n' +
					'Do not forget to add details about what you have done before error appeared. \n \n' +
					'Now you will be forwarded to homepage.');
			}
			window.location.href = window.location.origin + '/clear-session';
		} else {
			console.warn('UNHANDLED STATUS: ', status)
		}
	});
	await new Promise(resolve => setTimeout(resolve, 1000));
	if (!STOPPED) return getstatus();
}

async function submit() {
	// clearInterval(GETSTATUS_INTERVAL);
	STOPPED = true;
	hide_login();
	loading_start();
	const uname = document.getElementById("uname").value.trim();
	const upswd = document.getElementById("upswd").value.trim();
	if (uname === "" || upswd === "") return;
	console.log("submit");
	STOPPED = false;
	sendData("/login", "POST", {
		uname: uname,
		upswd: upswd,
	}).then((response) => {
		console.log(response);
	});
	// GETSTATUS_INTERVAL = setInterval(getstatus, 1000);
	await new Promise(resolve => setTimeout(resolve, 1000));
	return getstatus();
}

async function sendData(url = "", method = "POST", data = "") {
	let request = {
		method: method,
		cache: "no-cache",
		mode: "same-origin", // no-cors, *cors, same-origin
		credentials: "same-origin",
		headers: {
			"Content-Type": "application/json",
		},
	};
	if (data !== "") {
		request.body = JSON.stringify(data);
	}
	const response = await fetch(url, request).then((r) => r.json());
	if (response.OK === false) {
		console.error("REQUEST ERROR");
		return false;
	}
	return response;
}

function showresults(PDATA) {
	const section = document.querySelector(".results");
	const profile = document.querySelector(".profile");
	const content = document.querySelector(".content");
	profile.querySelector("span").textContent = PDATA.user;
	profile.querySelector("img").setAttribute("src", PDATA.avatar);
	content.innerHTML =
		generalinfo(PDATA) + fandomsinfo(PDATA) + fanficsinfo(PDATA);
	try {
		document
			.getElementById("showallfanfics-btn")
			.addEventListener("click", () => showallfanfics(PDATA));
		document
			.getElementById("showallfandoms-btn")
			.addEventListener("click", () => showallfandoms(PDATA));
	} catch (e) {}
	section.classList.remove("hidden");
	loading_stop();

	function generalinfo(PDATA) {
		if (document.querySelector('html').getAttribute('lang') === 'ru') {
			return `
				<ul>
					Общая информация:
					<li>Всего страниц прочитано: <span>${PDATA.pageCount}</span></li>
					<li>Всего фанфиков прочитано: <span>${PDATA.fanfics.length}</span></li>
					<li>Наиболее читаемый фэндом: '<span>${PDATA.fandoms[0].name}</span>' с <span>${PDATA.fandoms[0].amount}</span> прочитанными фанфиками.</li>
					<li>Послежний прочитанный фанфик: '<span>${PDATA.fanfics[0].title}</span>' от '<span>${PDATA.fanfics[0].fandom}</span>'.</li>
				</ul>
			`;
		}
		return `
            <ul>
                General info:
                <li>Total pages read: <span>${PDATA.pageCount}</span></li>
                <li>Total fanfics read: <span>${PDATA.fanfics.length}</span></li>
                <li>The most liked fandom is '<span>${PDATA.fandoms[0].name}</span>' with <span>${PDATA.fandoms[0].amount}</span> fanfics read.</li>
                <li>The most recently you read '<span>${PDATA.fanfics[0].title}</span>' from '<span>${PDATA.fanfics[0].fandom}</span>'.</li>
            </ul>
        `;
	}
	function fandomsinfo(PDATA) {
		let r;
		if (document.querySelector('html').getAttribute('lang') === 'ru') {
			r = `<ol id="fandoms">Топ 10 фэндомов (Имя фэндома — количество прочитанных фанфиков):`;
		} else {
			r = `<ol id="fandoms">Top 10 fandoms info (Fandom name — number of fanfics you read):`;
		}
		for (let i = 0; i < Math.min(10, PDATA.fandoms.length); i++) {
			r += `<li>${PDATA.fandoms[i].name} — ${PDATA.fandoms[i].amount}</li>`;
		}
		if (PDATA.fandoms.length > 10) {
			if (document.querySelector('html').getAttribute('lang') === 'ru') {
				r += `<a href="#fandoms" id="showallfandoms-btn">Показать все</a>`;
			} else {
				r += `<a href="#fandoms" id="showallfandoms-btn">Show all</a>`;
			}
		}
		r += `</ol>`;
		return r;
	}
	function fanficsinfo(PDATA) {
		let r;
		if (document.querySelector('html').getAttribute('lang') === 'ru') {
			r = `<ol id="fanfics">Последние 10 фанфиков (Название фанфика (размер) — фэндом):`;
		} else {
			r = `<ol id="fanfics">Last 10 fanfics info (Fanfic name (size) — fandom):`;
		}
		for (let i = 0; i < Math.min(10, PDATA.fanfics.length); i++) {
			r += `<li>${PDATA.fanfics[i].title} (${
				PDATA.fanfics[i].size
			}) — ${PDATA.fanfics[i].fandom.join(", ")}</li>`;
		}
		if (PDATA.fanfics.length > 10) {
			r += `<a href="#fanfics" id="showallfanfics-btn">${
				document.querySelector('html').getAttribute('lang') === 'ru' 
					? 'Показать все' : 'Show all'
			}</a>`;
		}
		r += `</ol>`;
		return r;
	}
}

function showallfandoms(PDATA) {
	if (PDATA.fandoms.length <= 10) return;
	const fandoms_ul = document.getElementById("fandoms");
	fandoms_ul.querySelector("#showallfandoms-btn").remove();
	for (let i = 10; i < PDATA.fandoms.length; i++) {
		fandoms_ul.innerHTML += `<li>${PDATA.fandoms[i].name} — ${PDATA.fandoms[i].amount}</li>`;
	}
}

function showallfanfics(PDATA) {
	if (PDATA.fanfics.length <= 10) return;
	const fanfics_ul = document.getElementById("fanfics");
	fanfics_ul.querySelector("#showallfanfics-btn").remove();
	for (let i = 10; i < PDATA.fanfics.length; i++) {
		fanfics_ul.innerHTML += `<li>${PDATA.fanfics[i].title} (${
			PDATA.fanfics[i].size
		}) — ${PDATA.fanfics[i].fandom.join(", ")}</li>`;
	}
}
