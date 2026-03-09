import { test, expect } from '@playwright/test';

const targetUrl = 'http://192.168.10.25:8000/';

async function collectOverflow(page) {
  return await page.evaluate(() => {
    const root = document.documentElement;
    const body = document.body;
    const global = {
      docScrollW: root.scrollWidth,
      docClientW: root.clientWidth,
      bodyScrollW: body ? body.scrollWidth : 0,
      bodyClientW: body ? body.clientWidth : 0,
      hasGlobalHorizontalOverflow:
        root.scrollWidth > root.clientWidth + 1 || (body && body.scrollWidth > body.clientWidth + 1),
    };

    const offenders = [];
    for (const el of Array.from(document.querySelectorAll('*'))) {
      const cs = window.getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      const hasOverflowX = el.scrollWidth > el.clientWidth + 1;
      const extendsPastViewport = rect.right > window.innerWidth + 1 || rect.left < -1;
      const ignoreByDesign = ['auto', 'scroll', 'hidden', 'clip'].includes(cs.overflowX);
      if ((hasOverflowX || extendsPastViewport) && !ignoreByDesign) {
        offenders.push({
          tag: el.tagName,
          id: el.id || null,
          className: el.className || null,
          scrollWidth: el.scrollWidth,
          clientWidth: el.clientWidth,
          right: Math.round(rect.right),
          viewportW: window.innerWidth,
          overflowX: cs.overflowX,
        });
      }
    }

    return { global, offenders: offenders.slice(0, 20) };
  });
}

test.describe('mytube smoke + overflow', () => {
  for (const vp of [
    { name: 'desktop', width: 1440, height: 900 },
    { name: 'mobile', width: 390, height: 844 },
  ]) {
    test(`smoke ${vp.name}`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      const resp = await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
      expect(resp && resp.status()).toBe(200);

      await expect(page.locator('#app')).toBeVisible();
      await page.waitForTimeout(1500);

      const overflow = await collectOverflow(page);
      console.log(`VIEWPORT=${vp.name} OVERFLOW=${JSON.stringify(overflow)}`);

      await page.screenshot({ path: `tests_e2e/mytube-smoke-${vp.name}.png`, fullPage: true });

      expect(overflow.global.hasGlobalHorizontalOverflow).toBeFalsy();
      expect(overflow.offenders.length).toBe(0);
    });
  }
});
