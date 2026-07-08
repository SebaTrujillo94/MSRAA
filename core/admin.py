from django.contrib import admin
from django.contrib import messages
from django.urls import path
from django.template.response import TemplateResponse
from django.utils.html import format_html, mark_safe
from django.utils import timezone
from django.db import models as db_models
from solo.admin import SingletonModelAdmin
from .models import (
    SiteConfiguration, MenuItem, HeroVideo,
    ClientLogo, PortfolioCategory, PortfolioProject, PortfolioProjectImage,
    CurriculumItem, CurriculumItemImage, MediaItem, MediaItemImage,
    MediaItemSection, MediaItemVideo,
    ContactSubmission,
)


def _safe_save(admin_instance, request, obj, form, change):
    """Save model using queryset.update() to bypass pre_save on FileFields."""
    file_field_names = [
        f.name for f in obj._meta.fields
        if isinstance(f, (db_models.FileField, db_models.ImageField))
    ]
    file_fields_changed = any(f in form.changed_data for f in file_field_names)

    if change and not file_fields_changed and file_field_names:
        update_vals = {
            f.attname: getattr(obj, f.attname)
            for f in obj._meta.fields
            if not isinstance(f, (db_models.FileField, db_models.ImageField))
            and f.name != 'id'
        }
        obj.__class__.objects.filter(pk=obj.pk).update(**update_vals)
    else:
        try:
            obj.save()
        except Exception as e:
            if 'cloudinary' in str(e).lower() or 'forbidden' in str(e).lower():
                if change:
                    update_vals = {
                        f.attname: getattr(obj, f.attname)
                        for f in obj._meta.fields
                        if not isinstance(f, (db_models.FileField, db_models.ImageField))
                        and f.name != 'id'
                    }
                    obj.__class__.objects.filter(pk=obj.pk).update(**update_vals)
                    messages.warning(request, 'Guardado sin imagen — actualiza CLOUDINARY_URL en Vercel env vars.')
                else:
                    raise
            else:
                raise


def _cld_init():
    """Configure Cloudinary SDK from env. Returns error string or None."""
    import os, re
    from django.conf import settings
    import cloudinary
    cld_env = (
        os.environ.get('CLOUDINARY_URL') or
        getattr(settings, 'CLOUDINARY_STORAGE', {}).get('CLOUDINARY_URL', '')
    )
    m = re.match(r'cloudinary://([^:]+):([^@]+)@(.+)', cld_env or '')
    if not m:
        return 'CLOUDINARY_URL no configurada en Vercel env vars'
    cloudinary.config(api_key=m.group(1), api_secret=m.group(2), cloud_name=m.group(3))
    return None


_EAGER_VIDEO = [{
    'video_codec': 'h264',
    'audio_codec': 'aac',
    'width': 1920,
    'height': 1080,
    'crop': 'limit',
    'quality': 'auto:good',
    'format': 'mp4',
}]

_CROP_PREVIEW_TMPL = """
<style>
@keyframes cce-spin{to{transform:rotate(360deg)}}
.cce-cell-ACT{background:#142040!important;border-color:#3a70c0!important;color:#70b0f0!important;box-shadow:0 0 10px rgba(58,112,192,.35)!important}
</style>
<div id="cce-__WID__" style="background:#16182a;border:1px solid #252840;border-radius:10px;padding:18px;max-width:720px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin-top:10px;box-shadow:0 4px 20px rgba(0,0,0,.3)">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid #252840">
    <span style="font-size:18px">🎨</span>
    <span style="font-weight:700;font-size:12px;color:#a0aac8;letter-spacing:1px;text-transform:uppercase">Editor de Recorte</span>
    <span id="cce-badge-__WID__" style="margin-left:auto;font-size:10px;padding:3px 10px;border-radius:10px;background:#252840;color:#506080;font-weight:700;letter-spacing:.8px">SIN IMAGEN</span>
  </div>
  <div style="display:flex;gap:16px;align-items:flex-start">
    <div style="flex:1;min-width:0">
      <div style="font-size:10px;color:#506080;margin-bottom:6px;text-transform:uppercase;letter-spacing:.8px;font-weight:700">Vista Previa</div>
      <div style="background:#0c0e1a;border-radius:6px;overflow:hidden;border:1px solid #252840">
        <div id="cce-frame-__WID__" style="width:100%;padding-top:56.25%;position:relative;transition:padding-top .4s ease">
          <img id="cce-img-__WID__" style="position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover;display:none;transition:opacity .3s">
          <div id="cce-spinner-__WID__" style="position:absolute;inset:0;display:none;align-items:center;justify-content:center;background:#0c0e1a">
            <div style="width:28px;height:28px;border:3px solid #252840;border-top-color:#4a80c0;border-radius:50%;animation:cce-spin .9s linear infinite"></div>
          </div>
          <div id="cce-ph-__WID__" style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#303450;font-size:12px;gap:10px;text-align:center;padding:20px">
            <span style="font-size:36px;opacity:.4">🖼️</span>
            <span>Sube una imagen a Cloudinary<br>para activar el editor de recorte</span>
          </div>
          <div id="cce-overlay-__WID__" style="position:absolute;bottom:0;left:0;right:0;background:linear-gradient(transparent,rgba(0,0,0,.65));padding:14px 12px 8px;display:none">
            <div style="font-size:9px;color:rgba(255,255,255,.35);letter-spacing:.8px;text-transform:uppercase">Título del elemento</div>
          </div>
        </div>
      </div>
      <div style="display:flex;justify-content:space-between;margin-top:6px;padding:0 2px">
        <span id="cce-ratio-lbl-__WID__" style="font-size:10px;color:#506080;font-family:monospace">—</span>
        <span id="cce-dims-__WID__" style="font-size:10px;color:#506080;font-family:monospace">—</span>
      </div>
    </div>
    <div style="flex-shrink:0;width:140px">
      <div style="font-size:10px;color:#506080;margin-bottom:6px;text-transform:uppercase;letter-spacing:.8px;font-weight:700">Punto de enfoque</div>
      <div id="cce-grid-__WID__" style="display:grid;grid-template-columns:repeat(3,40px);gap:3px;margin-bottom:10px">
        <div data-g="northwest" style="height:40px;background:#0c0e1a;border:1px solid #252840;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:12px;color:#3a4060;transition:all .15s">↖</div>
        <div data-g="north" style="height:40px;background:#0c0e1a;border:1px solid #252840;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:12px;color:#3a4060;transition:all .15s">↑</div>
        <div data-g="northeast" style="height:40px;background:#0c0e1a;border:1px solid #252840;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:12px;color:#3a4060;transition:all .15s">↗</div>
        <div data-g="west" style="height:40px;background:#0c0e1a;border:1px solid #252840;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:12px;color:#3a4060;transition:all .15s">←</div>
        <div data-g="center" style="height:40px;background:#0c0e1a;border:1px solid #252840;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:15px;color:#3a4060;transition:all .15s">⊙</div>
        <div data-g="east" style="height:40px;background:#0c0e1a;border:1px solid #252840;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:12px;color:#3a4060;transition:all .15s">→</div>
        <div data-g="southwest" style="height:40px;background:#0c0e1a;border:1px solid #252840;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:12px;color:#3a4060;transition:all .15s">↙</div>
        <div data-g="south" style="height:40px;background:#0c0e1a;border:1px solid #252840;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:12px;color:#3a4060;transition:all .15s">↓</div>
        <div data-g="southeast" style="height:40px;background:#0c0e1a;border:1px solid #252840;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:12px;color:#3a4060;transition:all .15s">↘</div>
      </div>
      <div id="cce-special-__WID__" style="display:none;text-align:center;padding:8px 6px;background:#0c0e1a;border:1px solid #252840;border-radius:4px;margin-bottom:12px">
        <div id="cce-si-__WID__" style="font-size:22px">🤖</div>
        <div id="cce-sl-__WID__" style="font-size:9px;color:#506080;margin-top:3px;line-height:1.3">Detección automática</div>
      </div>
      <div style="font-size:10px;color:#506080;margin-bottom:6px;text-transform:uppercase;letter-spacing:.8px;font-weight:700">Tarjeta (3:2)</div>
      <div style="width:100%;padding-top:66.67%;position:relative;background:#0c0e1a;border:1px solid #252840;border-radius:4px;overflow:hidden">
        <img id="cce-thumb-__WID__" style="position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover;display:none">
        <div id="cce-tph-__WID__" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#303450;font-size:22px;opacity:.4">🖼️</div>
      </div>
    </div>
  </div>
  <div style="margin-top:14px;padding-top:14px;border-top:1px solid #252840">
    <div style="font-size:10px;color:#506080;margin-bottom:6px;text-transform:uppercase;letter-spacing:.8px;font-weight:700">URL Cloudinary generada</div>
    <div style="display:flex;gap:8px;align-items:stretch">
      <code id="cce-url-__WID__" style="flex:1;background:#0c0e1a;border:1px solid #1a1c2e;border-radius:4px;padding:7px 10px;font-size:9px;color:#4a5870;word-break:break-all;line-height:1.6;transition:color .3s">
        Esperando URL de Cloudinary...
      </code>
      <button type="button" id="cce-copy-__WID__" style="padding:7px 14px;background:#182040;border:1px solid #2a3560;border-radius:4px;color:#4a70b0;font-size:10px;cursor:pointer;white-space:nowrap;font-weight:700;transition:all .15s;flex-shrink:0">
        Copiar
      </button>
    </div>
  </div>
</div>
<script>
(function(){
  var wid='__WID__';
  var RATIO_PAD={'':56.25,'16:9':56.25,'4:3':75,'3:2':66.67,'1:1':100,'2:3':150};
  var RATIO_LBL={'':'Original','16:9':'16:9 — Panorámico','4:3':'4:3 — Clásico','3:2':'3:2 — Foto','1:1':'1:1 — Cuadrado','2:3':'2:3 — Retrato'};
  var SPEC_G={'auto':['🤖','Detección automática (IA)'],'face':['😶','Enfoca en cara detectada'],'faces':['👥','Enfoca en todas las caras']};
  function $i(id){return document.getElementById(id);}
  var frame=$i('cce-frame-'+wid),img=$i('cce-img-'+wid),spinner=$i('cce-spinner-'+wid);
  var ph=$i('cce-ph-'+wid),badge=$i('cce-badge-'+wid),ratioLbl=$i('cce-ratio-lbl-'+wid);
  var dims=$i('cce-dims-'+wid),urlEl=$i('cce-url-'+wid),grid=$i('cce-grid-'+wid);
  var special=$i('cce-special-'+wid),si=$i('cce-si-'+wid),sl=$i('cce-sl-'+wid);
  var thumb=$i('cce-thumb-'+wid),tph=$i('cce-tph-'+wid),overlay=$i('cce-overlay-'+wid);
  var copyBtn=$i('cce-copy-'+wid),curUrl='';
  function setBadge(t,bg,c){badge.textContent=t;badge.style.background=bg;badge.style.color=c;}
  function updateGrid(g){
    var cells=grid.querySelectorAll('[data-g]');
    if(SPEC_G[g]){
      special.style.display='block';si.textContent=SPEC_G[g][0];sl.textContent=SPEC_G[g][1];
      cells.forEach(function(c){c.style.background='#0c0e1a';c.style.borderColor='#252840';c.style.color='#3a4060';c.style.boxShadow='none';});
    } else {
      special.style.display='none';
      cells.forEach(function(c){
        var on=c.getAttribute('data-g')===g;
        c.style.background=on?'#142040':'#0c0e1a';
        c.style.borderColor=on?'#3a70c0':'#252840';
        c.style.color=on?'#70b0f0':'#3a4060';
        c.style.boxShadow=on?'0 0 10px rgba(58,112,192,.35)':'none';
      });
    }
  }
  // Strip any existing transforms/version from Cloudinary URL, return clean /upload/path
  function strip(url){
    var idx=url.indexOf('/upload/');
    if(idx<0)return url;
    var segs=url.slice(idx+8).split('/');
    var ver='',i=0;
    while(i<segs.length){
      var s=segs[i];
      if(/^v\d+$/.test(s)){ver=s;i++;break;}
      if(/[,]/.test(s)||/^[a-z]{1,3}_/.test(s)){i++;continue;}
      break;
    }
    return url.slice(0,idx+8)+(ver?ver+'/':'')+segs.slice(i).join('/');
  }
  function buildUrl(url,g,r){
    var parts=['f_auto','q_auto:good','c_fill','g_'+(g||'auto'),'w_600'];
    if(r)parts.push('ar_'+r);
    return strip(url).replace('/upload/','/upload/'+parts.join(',')+'/');
  }
  function buildThumb(url,g){
    var parts=['f_auto','q_auto:good','c_fill','g_'+(g||'auto'),'w_300','ar_3:2'];
    return strip(url).replace('/upload/','/upload/'+parts.join(',')+'/');
  }
  // Read transforms already embedded in URL and sync dropdowns (only if still at default)
  function detectFromUrl(url){
    if(!url||url.indexOf('res.cloudinary.com')<0)return;
    var idx=url.indexOf('/upload/');
    if(idx<0)return;
    var segs=url.slice(idx+8).split('/');
    var tSegs=[];
    for(var i=0;i<segs.length;i++){
      var s=segs[i];
      if(/^v\d+$/.test(s))break;
      if(/[,]/.test(s)||/^[a-z]{1,3}_/.test(s))tSegs.push(s);
      else break;
    }
    if(!tSegs.length)return;
    var allT=tSegs.join(',');
    var gf=$i('__GRAV_FID__'),rf=$i('__RAT_FID__');
    // Sync gravity if dropdown is at default 'auto'
    if(gf&&gf.value==='auto'){
      var gm=allT.match(/(?:^|,)g_([a-z]+)/);
      if(gm){
        var gopts=[].slice.call(gf.options).map(function(o){return o.value;});
        if(gopts.indexOf(gm[1])>=0)gf.value=gm[1];
      }
    }
    // Sync ratio if dropdown is at default ''
    if(rf&&rf.value===''){
      var rm=allT.match(/(?:^|,)ar_([0-9]+:[0-9]+)/);
      if(rm){
        var ropts=[].slice.call(rf.options).map(function(o){return o.value;});
        if(ropts.indexOf(rm[1])>=0)rf.value=rm[1];
      }
    }
  }
  function update(){
    var uf=$i('__URL_FID__'),gf=$i('__GRAV_FID__'),rf=$i('__RAT_FID__');
    var url=uf?uf.value.trim():'',g=gf?gf.value:'auto',r=rf?rf.value:'';
    updateGrid(g);
    var pad=RATIO_PAD[r]!==undefined?RATIO_PAD[r]:56.25;
    frame.style.paddingTop=pad+'%';
    ratioLbl.textContent=RATIO_LBL[r]||'Original';
    if(!url||url.indexOf('res.cloudinary.com')<0){
      img.style.display='none';spinner.style.display='none';ph.style.display='flex';
      overlay.style.display='none';thumb.style.display='none';tph.style.display='flex';
      setBadge('SIN IMAGEN','#252840','#506080');
      urlEl.textContent='Esperando URL de Cloudinary...';dims.textContent='—';curUrl='';
      return;
    }
    var purl=buildUrl(url,g,r),turl=buildThumb(url,g);
    curUrl=purl;urlEl.textContent=purl;
    var w=600,h=Math.round(w*pad/100);
    dims.textContent=w+' × '+h+' px';
    img.style.opacity='0';spinner.style.display='flex';ph.style.display='none';
    setBadge('CARGANDO','#1a2a14','#60a040');
    img.onload=function(){
      spinner.style.display='none';img.style.display='block';img.style.opacity='1';
      overlay.style.display='block';setBadge('ACTIVO','#142a1a','#40c060');
    };
    img.onerror=function(){
      spinner.style.display='none';ph.style.display='flex';img.style.display='none';
      setBadge('ERROR','#2a1414','#c04040');
    };
    img.src=purl;
    thumb.onload=function(){thumb.style.display='block';tph.style.display='none';};
    thumb.src=turl;
  }
  copyBtn.addEventListener('click',function(){
    if(!curUrl)return;
    if(navigator.clipboard){
      navigator.clipboard.writeText(curUrl).then(function(){
        copyBtn.textContent='✓ Copiado!';copyBtn.style.color='#40c060';copyBtn.style.borderColor='#30a050';
        setTimeout(function(){copyBtn.textContent='Copiar';copyBtn.style.color='#4a70b0';copyBtn.style.borderColor='#2a3560';},1800);
      });
    }
  });
  ['__URL_FID__','__GRAV_FID__','__RAT_FID__'].forEach(function(id){
    var el=$i(id);
    if(el){el.addEventListener('change',update);el.addEventListener('input',update);}
  });
  // Auto-init: detect transforms already in URL, then render preview
  function init(){
    var uf=$i('__URL_FID__');
    var url=uf?uf.value.trim():'';
    detectFromUrl(url);
    update();
  }
  if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',init);}
  else{setTimeout(init,100);}
  setTimeout(init,600); // fallback for slow admin JS
})();
</script>
"""


class CloudinaryUploadMixin:
    """
    Mixin for ModelAdmin classes that adds Cloudinary upload buttons.

    Configure per admin class:
        cld_video_field = 'video_url'       # URLField for video (None to disable)
        cld_image_field = 'image_url'       # URLField for image (None to disable)
        cld_folder      = 'msraa/videos'    # Cloudinary folder prefix (auto if None)
    """
    cld_video_field = 'video_url'
    cld_image_field = None
    cld_folder = None

    def get_urls(self):
        urls = super().get_urls()
        mn = self.model._meta.model_name
        custom = [
            path(
                'inline-upload-cld/',
                self.admin_site.admin_view(self._cld_inline_upload_view),
                name=f'{mn}_inline_cld_upload',
            ),
        ]
        if self.cld_video_field:
            custom.append(path(
                '<int:pk>/upload-cld-video/',
                self.admin_site.admin_view(self._cld_video_view),
                name=f'{mn}_upload_cld_video',
            ))
        if self.cld_image_field:
            custom.append(path(
                '<int:pk>/upload-cld-image/',
                self.admin_site.admin_view(self._cld_image_view),
                name=f'{mn}_upload_cld_image',
            ))
        return custom + urls

    def _cld_inline_upload_view(self, request):
        """Upload a URL to Cloudinary without saving to DB. Returns {url}."""
        import json, hashlib
        from django.http import JsonResponse
        if request.method != 'POST':
            return JsonResponse({'error': 'POST only'}, status=405)
        try:
            data = json.loads(request.body)
            source_url = data.get('url', '').strip()
            resource_type = data.get('resource_type', 'image')
            if resource_type not in ('image', 'video'):
                resource_type = 'image'
        except Exception:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        if not source_url:
            return JsonResponse({'error': 'URL requerida'}, status=400)
        from .models import _resolve_media_url
        import cloudinary.uploader
        err = _cld_init()
        if err:
            return JsonResponse({'error': err}, status=500)
        mn = self.model._meta.model_name
        folder = self.cld_folder or f'msraa/{mn}'
        pid = hashlib.md5(source_url.encode()).hexdigest()[:12]
        try:
            kwargs = dict(
                resource_type=resource_type,
                folder=folder,
                public_id=f'{mn}_inline_{pid}',
                overwrite=True,
            )
            if resource_type == 'video':
                kwargs.update(eager=_EAGER_VIDEO, eager_async=True)
            result = cloudinary.uploader.upload(_resolve_media_url(source_url), **kwargs)
            return JsonResponse({'url': result['secure_url']})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def _cld_upload(self, source_url, resource_type, pk, eager=None):
        """Upload source_url to Cloudinary. Returns (secure_url, error)."""
        from .models import _resolve_media_url
        import cloudinary.uploader
        err = _cld_init()
        if err:
            return None, err
        mn = self.model._meta.model_name
        folder = self.cld_folder or f'msraa/{mn}'
        resolved = _resolve_media_url(source_url)
        try:
            kwargs = dict(
                resource_type=resource_type,
                folder=folder,
                public_id=f'{mn}_{pk}',
                overwrite=True,
            )
            if eager:
                kwargs.update(eager=eager, eager_async=True)
            result = cloudinary.uploader.upload(resolved, **kwargs)
            return result['secure_url'], None
        except Exception as e:
            return None, str(e)

    def _cld_video_view(self, request, pk):
        import json
        from django.http import JsonResponse
        if request.method != 'POST':
            return JsonResponse({'error': 'POST only'}, status=405)
        try:
            source_url = json.loads(request.body).get('url', '').strip()
        except Exception:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        if not source_url:
            return JsonResponse({'error': 'URL requerida'}, status=400)
        url, error = self._cld_upload(source_url, 'video', pk, eager=_EAGER_VIDEO)
        if error:
            return JsonResponse({'error': error}, status=500)
        self.model.objects.filter(pk=pk).update(**{self.cld_video_field: url})
        return JsonResponse({'url': url})

    def _cld_image_view(self, request, pk):
        import json
        from django.http import JsonResponse
        if request.method != 'POST':
            return JsonResponse({'error': 'POST only'}, status=405)
        try:
            source_url = json.loads(request.body).get('url', '').strip()
        except Exception:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        if not source_url:
            return JsonResponse({'error': 'URL requerida'}, status=400)
        url, error = self._cld_upload(source_url, 'image', pk)
        if error:
            return JsonResponse({'error': error}, status=500)
        self.model.objects.filter(pk=pk).update(**{self.cld_image_field: url})
        return JsonResponse({'url': url})

    def _crop_preview(self, obj, url_field_id, gravity_field_id, ratio_field_id, widget_id=''):
        wid = widget_id or url_field_id.replace('id_', '').replace('-', '_')
        html = (_CROP_PREVIEW_TMPL
                .replace('__WID__', wid)
                .replace('__URL_FID__', url_field_id)
                .replace('__GRAV_FID__', gravity_field_id)
                .replace('__RAT_FID__', ratio_field_id))
        return mark_safe(html)

    @admin.display(description='Vista previa recorte')
    def crop_preview_image(self, obj):
        return self._crop_preview(obj, 'id_image_url', 'id_img_gravity', 'id_img_ratio')

    @admin.display(description='Vista previa recorte')
    def crop_preview_hero(self, obj):
        return self._crop_preview(obj, 'id_hero_image_url', 'id_img_gravity', 'id_img_ratio', 'hero')

    @admin.display(description='')
    def inline_cloudinary_btns(self, obj):
        """Injects JS that adds individual upload buttons to every inline URL field."""
        if not obj or not obj.pk:
            return mark_safe('')
        mn = self.model._meta.model_name
        upload_url = f'/admin/core/{mn}/inline-upload-cld/'
        js = (
            '<span style="display:none" id="cld-inline-helper">'
            '<script>(function(){'
            'var UPL="__URL__";'
            'function csrf(){var t=document.querySelector("[name=csrfmiddlewaretoken]");return t?t.value:"";}'
            'function addBtns(root){'
            '(root||document).querySelectorAll("input[name$=\\"-image_url\\"],input[name$=\\"-video_url\\"]").forEach(function(inp){'
            'if(inp.dataset.cldDone)return;inp.dataset.cldDone="1";'
            'var isVid=inp.name.endsWith("-video_url");'
            'var lbl=isVid?"☁️ Subir video":"🖼️ Subir imagen";'
            'var sp=document.createElement("span");sp.style="margin-left:6px";'
            'var btn=document.createElement("button");btn.type="button";btn.textContent=lbl;'
            'btn.style="padding:3px 9px;background:#e05d20;color:#fff;border:none;border-radius:3px;cursor:pointer;font-size:11px;font-weight:600;margin-left:4px";'
            'var st=document.createElement("span");st.style="margin-left:6px;font-size:11px";'
            'btn.onclick=function(){'
            'var url=inp.value.trim();'
            'if(!url){st.style.color="#c00";st.textContent="❌ Ingresa URL";return;}'
            'btn.disabled=true;btn.textContent="⏳...";st.textContent="";'
            'fetch(UPL,{method:"POST",headers:{"Content-Type":"application/json","X-CSRFToken":csrf()},body:JSON.stringify({url:url,resource_type:isVid?"video":"image"})})'
            '.then(function(r){return r.json();})'
            '.then(function(d){'
            'btn.textContent=lbl;btn.disabled=false;'
            'if(d.url){'
            'inp.value=d.url;st.style.color="green";st.textContent="✅";setTimeout(function(){st.textContent="";},3000);'
            'if(!isVid&&d.url.indexOf("res.cloudinary.com")>=0){'
            'var row=inp.closest("tr")||inp.closest(".dynamic-form");'
            'if(row){'
            'var pkInp=row.querySelector("input[name$=\\"-id\\"]");'
            'var edCell=row.querySelector(".inline-editor-cell[data-pk]");'
            'var pk=edCell?edCell.getAttribute("data-pk"):(pkInp?pkInp.value:"");'
            'var mn=edCell?edCell.getAttribute("data-mn"):(inp.name.split("_set-")[0]||"");'
            'if(pk&&mn){'
            'var edSpan=row.querySelector(".inline-editor-cell");'
            'if(edSpan){edSpan.innerHTML="<a href=\'/admin/core/"+mn+"/"+pk+"/media-editor/\' target=\'_blank\' style=\'display:inline-block;padding:4px 10px;background:#142040;color:#70b0f0;border:1px solid #2a4080;border-radius:4px;font-size:11px;font-weight:700;text-decoration:none\'>✏️ Editar</a>";}'
            '}}}'
            '}'
            'else{st.style.color="#c00";st.textContent="❌ "+(d.error||"Error");}'
            '}).catch(function(){btn.textContent=lbl;btn.disabled=false;st.style.color="#c00";st.textContent="❌ Red";});'
            '};'
            'sp.appendChild(btn);sp.appendChild(st);'
            'inp.parentNode.insertBefore(sp,inp.nextSibling);'
            '});}'
            'if(document.readyState==="loading"){document.addEventListener("DOMContentLoaded",function(){addBtns();});}'
            'else{addBtns();}'
            'document.addEventListener("formset:added",function(e){addBtns(e.target||document);});'
            '})();</script></span>'
        ).replace('__URL__', upload_url)
        return mark_safe(js)

    def _cld_btn(self, obj, upload_path_suffix, field_id, icon, label, note):
        if not obj.pk:
            return format_html('<span style="color:#999">Guarda el registro primero</span>')
        slug = field_id.replace('id_', '').replace('-', '_')
        upload_path = f'/admin/core/{self.model._meta.model_name}/{obj.pk}/{upload_path_suffix}'
        return format_html(
            '''<div>
              <button type="button" id="cld-btn-{slug}"
                onclick="cldUp_{slug}()"
                style="padding:8px 18px;background:#e05d20;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:13px;font-weight:600;">
                {icon} {label}
              </button>
              <span id="cld-st-{slug}" style="margin-left:12px;font-size:13px;"></span>
              <p style="margin:5px 0 0;font-size:11px;color:#888">{note}</p>
            </div>
            <script>
            function cldUp_{slug}() {{
              var btn=document.getElementById('cld-btn-{slug}');
              var st=document.getElementById('cld-st-{slug}');
              var f=document.getElementById('{field_id}');
              var url=f?f.value.trim():'';
              if(!url){{st.style.color='#c00';st.textContent='❌ Ingresa una URL primero';return;}}
              btn.disabled=true;btn.textContent='⏳ Subiendo...';st.textContent='';
              var csrf=document.querySelector('[name=csrfmiddlewaretoken]').value;
              fetch('{upload_path}',{{method:'POST',headers:{{'Content-Type':'application/json','X-CSRFToken':csrf}},body:JSON.stringify({{url:url}})}})
              .then(r=>{{if(!r.ok)throw new Error('HTTP '+r.status);return r.json();}})
              .then(d=>{{
                if(d.url){{f.value=d.url;st.style.color='green';st.textContent='✅ Subido';btn.textContent='{icon} {label}';btn.disabled=false;}}
                else{{st.style.color='#c00';st.textContent='❌ '+(d.error||'Error');btn.disabled=false;btn.textContent='{icon} {label}';}}
              }}).catch(err=>{{st.style.color='#c00';st.textContent='❌ '+(err.message||'Error de red');btn.disabled=false;btn.textContent='{icon} {label}';}});
            }}
            </script>''',
            slug=slug, icon=icon, label=label, note=note,
            field_id=field_id, upload_path=upload_path,
        )

    @admin.display(description='☁️ Subir video a Cloudinary')
    def cloudinary_video_btn(self, obj):
        return self._cld_btn(
            obj, 'upload-cld-video/', f'id_{self.cld_video_field}',
            '☁️', 'Subir video a Cloudinary',
            'Descarga desde Dropbox y sube a Cloudinary CDN con H.264+1080p. Tarda 1–3 min.',
        )

    @admin.display(description='🖼️ Subir imagen a Cloudinary')
    def cloudinary_image_btn(self, obj):
        return self._cld_btn(
            obj, 'upload-cld-image/', f'id_{self.cld_image_field}',
            '🖼️', 'Subir imagen a Cloudinary',
            'Descarga desde Dropbox/Drive y sube a Cloudinary CDN con auto-calidad.',
        )


_GRAVITY_CHOICES_ADMIN = [
    ('northwest', '↖'), ('north', '↑'), ('northeast', '↗'),
    ('west', '←'), ('center', '⊙'), ('east', '→'),
    ('southwest', '↙'), ('south', '↓'), ('southeast', '↘'),
]

_SPECIAL_GRAVITY_ADMIN = [
    ('auto', '🤖 Auto (IA)'),
    ('face', '😶 Cara'),
    ('faces', '👥 Caras'),
]


class MediaEditorMixin(CloudinaryUploadMixin):
    """
    Extends CloudinaryUploadMixin with a full-page media editor.
    Requires 'core.edit_media_crop' permission (or superuser).

    Configure per admin class:
        editor_image_field = 'image_url'   # or 'hero_image_url'
        editor_video_field = 'video_url'   # or None
    """
    editor_image_field = None
    editor_video_field = 'video_url'

    def get_urls(self):
        urls = super().get_urls()
        mn = self.model._meta.model_name
        custom = [
            path('<int:pk>/media-editor/',
                 self.admin_site.admin_view(self._editor_view),
                 name=f'{mn}_media_editor'),
            path('<int:pk>/save-media-crop/',
                 self.admin_site.admin_view(self._save_crop_view),
                 name=f'{mn}_save_crop'),
            path('<int:pk>/delete-media-image/',
                 self.admin_site.admin_view(self._delete_media_image_view),
                 name=f'{mn}_delete_media_image'),
            path('<int:pk>/delete-media-video/',
                 self.admin_site.admin_view(self._delete_media_video_view),
                 name=f'{mn}_delete_media_video'),
        ]
        return custom + urls

    def _check_editor_perm(self, request):
        return request.user.is_superuser or request.user.has_perm('core.edit_media_crop')

    def _editor_view(self, request, pk):
        from django.http import HttpResponseForbidden, Http404
        if not self._check_editor_perm(request):
            return HttpResponseForbidden(
                '<h2>Sin permiso</h2><p>Necesitas el permiso <code>core.edit_media_crop</code>.</p>'
            )
        try:
            obj = self.model.objects.get(pk=pk)
        except self.model.DoesNotExist:
            raise Http404

        mn = self.model._meta.model_name
        image_url = (getattr(obj, self.editor_image_field, '') or '') if self.editor_image_field else ''
        video_url = (getattr(obj, self.editor_video_field, '') or '') if self.editor_video_field else ''

        # Context label for card mockup
        if hasattr(obj, 'tipo'):
            ctx_top = obj.get_tipo_display().upper()
        elif hasattr(obj, 'category') and obj.category:
            ctx_top = str(obj.category).upper()
        else:
            ctx_top = ''
        obj_year = getattr(obj, 'year', '') or ''

        # Video embed URL
        embed_url = ''
        if video_url and hasattr(obj, 'get_video_embed_url'):
            embed_url = obj.get_video_embed_url() or ''

        from .models import _RATIO_CHOICES
        ctx = dict(
            self.admin_site.each_context(request),
            title=f'Editor de Medios — {obj}',
            obj=obj,
            obj_pk=pk,
            obj_str=str(obj),
            mn=mn,
            image_url=image_url,
            video_url=video_url,
            embed_url=embed_url,
            img_x=int(getattr(obj, 'img_x', 0) or 0),
            img_y=int(getattr(obj, 'img_y', 0) or 0),
            img_crop_w=int(getattr(obj, 'img_crop_w', 0) or 0),
            img_crop_h=int(getattr(obj, 'img_crop_h', 0) or 0),
            ctx_top=ctx_top,
            obj_year=obj_year,
            change_url=f'/admin/core/{mn}/{pk}/change/',
            save_url=f'/admin/core/{mn}/{pk}/save-media-crop/',
            del_img_url=f'/admin/core/{mn}/{pk}/delete-media-image/',
            del_vid_url=f'/admin/core/{mn}/{pk}/delete-media-video/',
            ratio_choices=_RATIO_CHOICES,
            has_image=bool(image_url and 'res.cloudinary.com' in image_url),
            has_video=bool(video_url),
        )
        return TemplateResponse(request, 'admin/media_editor.html', ctx)

    def _save_crop_view(self, request, pk):
        import json
        from django.http import JsonResponse
        if request.method != 'POST':
            return JsonResponse({'error': 'POST only'}, status=405)
        if not self._check_editor_perm(request):
            return JsonResponse({'error': 'Sin permiso'}, status=403)
        try:
            data = json.loads(request.body)
            update = {}
            if 'img_x' in data:
                update['img_x'] = int(data['img_x'])
            if 'img_y' in data:
                update['img_y'] = int(data['img_y'])
            if 'img_crop_w' in data:
                update['img_crop_w'] = max(0, int(data['img_crop_w']))
            if 'img_crop_h' in data:
                update['img_crop_h'] = max(0, int(data['img_crop_h']))
            self.model.objects.filter(pk=pk).update(**update)
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def _delete_media_image_view(self, request, pk):
        from django.http import JsonResponse
        if request.method != 'POST':
            return JsonResponse({'error': 'POST only'}, status=405)
        if not self._check_editor_perm(request):
            return JsonResponse({'error': 'Sin permiso'}, status=403)
        if not self.editor_image_field:
            return JsonResponse({'error': 'Sin campo configurado'}, status=400)
        self.model.objects.filter(pk=pk).update(**{self.editor_image_field: ''})
        return JsonResponse({'status': 'ok'})

    def _delete_media_video_view(self, request, pk):
        from django.http import JsonResponse
        if request.method != 'POST':
            return JsonResponse({'error': 'POST only'}, status=405)
        if not self._check_editor_perm(request):
            return JsonResponse({'error': 'Sin permiso'}, status=403)
        if not self.editor_video_field:
            return JsonResponse({'error': 'Sin campo configurado'}, status=400)
        self.model.objects.filter(pk=pk).update(**{self.editor_video_field: ''})
        return JsonResponse({'status': 'ok'})

    @admin.display(description='🎨 Editor de Medios')
    def media_editor_btn(self, obj):
        if not obj.pk:
            return format_html('<span style="color:#999">Guarda el registro primero</span>')
        mn = self.model._meta.model_name
        url = f'/admin/core/{mn}/{obj.pk}/media-editor/'
        return format_html(
            '<a href="{}" target="_blank" '
            'style="display:inline-block;padding:9px 20px;background:#16213a;'
            'color:#5a90e0;border:1px solid #2a4080;border-radius:5px;'
            'text-decoration:none;font-size:13px;font-weight:700;letter-spacing:.3px;">'
            '🎨 Abrir Editor de Medios</a>'
            '<span style="margin-left:10px;font-size:11px;color:#888">'
            'Zoom · Encuadre · Recorte · Eliminar</span>',
            url,
        )


class PortfolioProjectImageInline(admin.TabularInline):
    model = PortfolioProjectImage
    extra = 2
    readonly_fields = ['image_editor_btn']
    fields = ['image', 'image_url', 'image_editor_btn', 'order']

    def image_editor_btn(self, obj):
        if not obj.pk:
            return mark_safe('<span class="inline-editor-cell" style="color:#506080;font-size:11px">Guarda primero</span>')
        has_cld = obj.image_url and 'res.cloudinary.com' in obj.image_url
        if not has_cld:
            return mark_safe(f'<span class="inline-editor-cell" data-pk="{obj.pk}" data-mn="portfolioprojectimage" style="color:#506080;font-size:11px">↑ Sube a Cloudinary</span>')
        url = f'/admin/core/portfolioprojectimage/{obj.pk}/media-editor/'
        return mark_safe(
            f'<span class="inline-editor-cell">'
            f'<a href="{url}" target="_blank" style="display:inline-block;padding:4px 10px;'
            f'background:#142040;color:#70b0f0;border:1px solid #2a4080;border-radius:4px;'
            f'font-size:11px;font-weight:700;text-decoration:none">✏️ Editar</a></span>'
        )
    image_editor_btn.short_description = 'Editor'


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(SingletonModelAdmin):
    readonly_fields = ('cloudinary_status_link',)
    fieldsets = (
        ('General', {
            'fields': ('site_title', 'tagline', 'logo_main', 'font_size_base', 'font_family'),
        }),
        ('Colores', {
            'fields': ('color_gold', 'color_gold_light', 'logo_sidebar_color'),
            'description': 'Colores de acento. logo_sidebar_color = color del logo pequeño izquierdo (por defecto rojo #CC0000).',
        }),
        ('Contacto y Redes', {
            'fields': ('contact_email', 'contact_phone', 'instagram_url', 'linkedin_url'),
        }),
        ('Hero Slides', {
            'fields': ('hero_slide_duration',),
            'description': 'Duración de cada slide en el video hero principal.',
        }),
        ('Sección About', {
            'fields': ('about_label', 'about_p1', 'about_p2'),
            'classes': ('collapse',),
        }),
        ('Estadísticas', {
            'fields': (
                'stat1_number', 'stat1_prefix', 'stat1_label',
                'stat2_number', 'stat2_prefix', 'stat2_label',
                'stat3_number', 'stat3_prefix', 'stat3_label',
            ),
            'classes': ('collapse',),
        }),
        ('Sección Clientes (Trust)', {
            'fields': ('trust_lbl', 'trust_title', 'trust_sub'),
            'classes': ('collapse',),
        }),
        ('Footer', {
            'fields': ('footer_copy',),
        }),
        ('Cloudinary — Almacenamiento', {
            'fields': ('cloudinary_status_link',),
            'description': 'Plan Free: 25 GB storage + 25 GB bandwidth/mes.',
        }),
    )

    @admin.display(description='Estado de uso')
    def cloudinary_status_link(self, obj):
        return format_html(
            '<a href="cloudinary/" class="button" style="padding:8px 16px;background:#0073aa;color:#fff;'
            'border-radius:4px;text-decoration:none;font-size:13px;">📊 Ver uso de Cloudinary</a>'
        )

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('cloudinary/', self.admin_site.admin_view(self._cloudinary_usage_view), name='cloudinary_usage'),
        ]
        return custom + urls

    def _cloudinary_usage_view(self, request):
        ctx = dict(self.admin_site.each_context(request), title='Estado Cloudinary')
        try:
            import cloudinary.api
            err = _cld_init()
            if err:
                raise Exception(err)
            usage = cloudinary.api.usage()
            storage_bytes = usage.get('storage', {}).get('usage', 0)
            bandwidth_bytes = usage.get('bandwidth', {}).get('usage', 0)
            GB = 1024 ** 3
            FREE_GB = 25
            ctx.update({
                'storage_gb': storage_bytes / GB,
                'storage_pct': min((storage_bytes / GB / FREE_GB) * 100, 100),
                'bandwidth_gb': bandwidth_bytes / GB,
                'bandwidth_pct': min((bandwidth_bytes / GB / FREE_GB) * 100, 100),
                'transformations': usage.get('transformations', {}).get('usage', 0),
                'requests': usage.get('requests', 0),
                'resources': usage.get('resources', 0),
                'now': timezone.now().strftime('%d/%m/%Y %H:%M'),
                'error': None,
            })
        except Exception as e:
            ctx.update({'error': str(e), 'storage_gb': 0, 'storage_pct': 0,
                        'bandwidth_gb': 0, 'bandwidth_pct': 0,
                        'transformations': 0, 'requests': 0, 'resources': 0, 'now': ''})
        return TemplateResponse(request, 'admin/cloudinary_usage.html', ctx)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['label', 'section_group', 'url', 'filter_value', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['section_group', 'is_active']
    ordering = ['section_group', 'order']


@admin.register(HeroVideo)
class HeroVideoAdmin(CloudinaryUploadMixin, admin.ModelAdmin):
    cld_video_field = 'video_url'
    cld_folder = 'msraa/hero'
    list_display = ['title_line1', 'title_line2', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    readonly_fields = ['cloudinary_video_btn']
    fields = [
        'title_line1', 'title_line1_en',
        'title_line2', 'title_line2_en',
        'video_file', 'video_url', 'cloudinary_video_btn',
        'order', 'is_active',
    ]
    actions = ['make_active', 'make_inactive']

    def save_model(self, request, obj, form, change):
        _safe_save(self, request, obj, form, change)

    @admin.action(description='✅ Activar seleccionados')
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='🚫 Desactivar seleccionados')
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(ClientLogo)
class ClientLogoAdmin(admin.ModelAdmin):
    list_display = ['logo_preview', 'name', 'display_scale', 'order', 'is_active']
    list_editable = ['display_scale', 'order', 'is_active']
    list_display_links = ['logo_preview', 'name']
    readonly_fields = ['logo_preview_large']
    fields = ['name', 'image', 'logo_preview_large', 'display_scale', 'website_url', 'order', 'is_active']

    @admin.display(description='Preview')
    def logo_preview(self, obj):
        from django.utils.html import format_html
        if obj.image:
            return format_html(
                '<img src="{}" style="height:40px;max-width:100px;object-fit:contain;background:#f5f5f5;padding:4px;border-radius:3px">',
                obj.image.url
            )
        return '—'

    @admin.display(description='Vista previa')
    def logo_preview_large(self, obj):
        from django.utils.html import format_html
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:80px;max-width:200px;object-fit:contain;background:#f0f0f0;padding:8px;border-radius:4px">',
                obj.image.url
            )
        return '—'


@admin.register(PortfolioCategory)
class PortfolioCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_en', 'slug', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(PortfolioProjectImage)
class PortfolioProjectImageAdmin(MediaEditorMixin, admin.ModelAdmin):
    cld_image_field = 'image_url'
    cld_folder = 'msraa/portfolio'
    editor_image_field = 'image_url'
    editor_video_field = None
    list_display = ['__str__', 'project', 'img_crop', 'order']
    list_filter = ['project']
    readonly_fields = ['cloudinary_image_btn', 'media_editor_btn']
    fields = ['project', 'image', 'image_url', 'cloudinary_image_btn', 'media_editor_btn', 'img_crop', 'img_gravity', 'img_ratio', 'img_zoom', 'img_x', 'img_y', 'img_bg', 'order']

    def save_model(self, request, obj, form, change):
        _safe_save(self, request, obj, form, change)


@admin.register(PortfolioProject)
class PortfolioProjectAdmin(MediaEditorMixin, admin.ModelAdmin):
    cld_video_field = 'video_url'
    cld_image_field = 'hero_image_url'
    cld_folder = 'msraa/portfolio'
    editor_image_field = 'hero_image_url'
    editor_video_field = 'video_url'
    list_display = ['title', 'category', 'year', 'location', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['category', 'is_active']
    inlines = [PortfolioProjectImageInline]
    readonly_fields = ['cloudinary_video_btn', 'cloudinary_image_btn', 'media_editor_btn', 'inline_cloudinary_btns']
    fields = [
        'title', 'title_en', 'category', 'year', 'location', 'location_en',
        'description', 'description_en',
        'hero_image', 'hero_image_url', 'cloudinary_image_btn', 'media_editor_btn',
        'video_url', 'cloudinary_video_btn',
        'inline_cloudinary_btns',
        'order', 'is_active',
    ]
    actions = ['make_active', 'make_inactive']

    def save_model(self, request, obj, form, change):
        _safe_save(self, request, obj, form, change)

    @admin.action(description='✅ Activar seleccionados')
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='🚫 Desactivar seleccionados')
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)


class CurriculumItemImageInline(admin.TabularInline):
    model = CurriculumItemImage
    extra = 2
    fields = ['image', 'image_url', 'caption', 'order']


@admin.register(CurriculumItem)
class CurriculumItemAdmin(CloudinaryUploadMixin, admin.ModelAdmin):
    cld_video_field = 'video_url'
    cld_folder = 'msraa/curriculum'
    inlines = [CurriculumItemImageInline]
    list_display = ['title', 'category', 'year', 'subtitle', 'url', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['category', 'is_active']
    ordering = ['category', 'order']
    readonly_fields = ['cloudinary_video_btn', 'inline_cloudinary_btns']
    fields = [
        'category', 'year', 'title', 'title_en', 'subtitle', 'subtitle_en',
        'url', 'url_label', 'url_label_en',
        'video_url', 'cloudinary_video_btn',
        'inline_cloudinary_btns',
        'order', 'is_active',
    ]
    actions = ['make_active', 'make_inactive']

    @admin.action(description='✅ Activar seleccionados')
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='🚫 Desactivar seleccionados')
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)


class MediaItemImageInline(admin.TabularInline):
    model = MediaItemImage
    extra = 2
    fields = ['image', 'image_url', 'caption', 'order']


class MediaItemSectionInline(admin.TabularInline):
    model = MediaItemSection
    extra = 1
    fields = ['title', 'body', 'order']


class MediaItemVideoInline(admin.TabularInline):
    model = MediaItemVideo
    extra = 1
    fields = ['video_url', 'caption', 'order']


@admin.register(MediaItem)
class MediaItemAdmin(MediaEditorMixin, admin.ModelAdmin):
    cld_video_field = 'video_url'
    cld_image_field = 'image_url'
    cld_folder = 'msraa/medios'
    editor_image_field = 'image_url'
    editor_video_field = 'video_url'
    inlines = [MediaItemSectionInline, MediaItemVideoInline, MediaItemImageInline]
    list_display = ['img_preview', 'title', 'tipo', 'year', 'url', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['tipo', 'is_active']
    list_display_links = ['img_preview', 'title']
    ordering = ['-year', 'order']
    readonly_fields = ['img_preview_large', 'cloudinary_video_btn', 'cloudinary_image_btn', 'media_editor_btn', 'inline_cloudinary_btns']
    fields = [
        'tipo', 'year', 'title', 'title_en',
        'description', 'description_en',
        'image', 'image_url', 'img_preview_large', 'cloudinary_image_btn', 'media_editor_btn',
        'url', 'url_label', 'url_label_en',
        'video_url', 'cloudinary_video_btn',
        'inline_cloudinary_btns',
        'order', 'is_active',
    ]
    actions = ['make_active', 'make_inactive']

    def save_model(self, request, obj, form, change):
        _safe_save(self, request, obj, form, change)

    @admin.action(description='✅ Activar seleccionados')
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='🚫 Desactivar seleccionados')
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)

    @admin.display(description='Imagen')
    def img_preview(self, obj):
        from django.utils.html import format_html
        if obj.image:
            return format_html('<img src="{}" style="height:40px;width:60px;object-fit:cover;border-radius:3px">', obj.image.url)
        return '—'

    @admin.display(description='Vista previa')
    def img_preview_large(self, obj):
        from django.utils.html import format_html
        if obj.image:
            return format_html('<img src="{}" style="max-height:200px;max-width:400px;object-fit:cover;border-radius:4px;margin-top:8px">', obj.image.url)
        return '—'


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'name', 'email', 'phone', 'project_type', 'short_message', 'is_read']
    list_display_links = ['created_at', 'name']
    list_filter = ['is_read', 'created_at']
    list_editable = ['is_read']
    search_fields = ['name', 'email', 'phone', 'message']
    readonly_fields = ['name', 'phone', 'email', 'project_type', 'message', 'created_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    actions = ['mark_read', 'mark_unread']

    @admin.display(description='Mensaje')
    def short_message(self, obj):
        return obj.message[:80] + '…' if len(obj.message) > 80 else obj.message

    @admin.action(description='Marcar como leído')
    def mark_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description='Marcar como no leído')
    def mark_unread(self, request, queryset):
        queryset.update(is_read=False)
